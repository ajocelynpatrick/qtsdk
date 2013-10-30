#!/usr/bin/env python
#############################################################################
##
## Copyright (C) 2013 Digia Plc and/or its subsidiary(-ies).
## Contact: http://www.qt-project.org/legal
##
## This file is part of the release tools of the Qt Toolkit.
##
## $QT_BEGIN_LICENSE:LGPL$
## Commercial License Usage
## Licensees holding valid commercial Qt licenses may use this file in
## accordance with the commercial license agreement provided with the
## Software or, alternatively, in accordance with the terms contained in
## a written agreement between you and Digia.  For licensing terms and
## conditions see http://qt.digia.com/licensing.  For further information
## use the contact form at http://qt.digia.com/contact-us.
##
## GNU Lesser General Public License Usage
## Alternatively, this file may be used under the terms of the GNU Lesser
## General Public License version 2.1 as published by the Free Software
## Foundation and appearing in the file LICENSE.LGPL included in the
## packaging of this file.  Please review the following information to
## ensure the GNU Lesser General Public License version 2.1 requirements
## will be met: http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
##
## In addition, as a special exception, Digia gives you certain additional
## rights.  These rights are described in the Digia Qt LGPL Exception
## version 1.1, included in the file LGPL_EXCEPTION.txt in this package.
##
## GNU General Public License Usage
## Alternatively, this file may be used under the terms of the GNU
## General Public License version 3.0 as published by the Free Software
## Foundation and appearing in the file LICENSE.GPL included in the
## packaging of this file.  Please review the following information to
## ensure the GNU General Public License version 3.0 requirements will be
## met: http://www.gnu.org/copyleft/gpl.html.
##
##
## $QT_END_LICENSE$
##
#############################################################################

# import the print function which is used in python 3.x
from __future__ import print_function

import itertools
# to get the cpu number
import multiprocessing
import os
import threading
import time
import Queue as queue # The Queue module has been renamed to queue in Python 3.
import sys
import __builtin__

# we are using RLock, because threadedPrint is using the same lock
outputLock = threading.RLock()
outputStates = None
outputFormatString = ''

# prepare our std output hooks
class StdOutHook:
    def write(self, text):
        # general print method sends line break just ignore that
        strippedText = text.strip()
        if strippedText == "":
            return
        global outputStates
        global outputFormatString
        localProgressIndicator = None
        if len(strippedText) > 6:
            localProgressIndicator = nextProgressIndicator()
        else:
            localProgressIndicator = strippedText

        newValue = "{:d}: {}".format(threadData.taskNumber, localProgressIndicator)
        with outputLock:
            if newValue != outputStates[threadData.workerThreadId]:
                oldOutput = "\r" + outputFormatString.format(*outputStates).strip()
                outputStates[threadData.workerThreadId] = newValue
                newOutput = "\r" + outputFormatString.format(*outputStates).strip()
                # cleanup old output if the new line is shorter
                cleanerString = ""
                if len(oldOutput) > len(newOutput):
                    cleanerString = " " * (len(oldOutput) - len(newOutput))

                sys.__stdout__.write(newOutput + cleanerString)

class StdErrHook:
    def write(self, text):
        with outputLock:
            sys.__stderr__.write(text)

# builtin print() isn't threadsafe, lets make it threadsafe
def threadedPrint(*a, **b):
    with outputLock:
        org_print(*a, **b)

def threadedExit(*a, **b):
    os._exit(*a, **b)

# this is really a HACK or better only useful in this complicate situation
__builtin__.org_print = __builtin__.print
__builtin__.org_stdout = sys.stdout
__builtin__.org_sterr = sys.stderr
__builtin__.org_exit = sys.exit

def enableThreadedPrint(enable = True, threadCount = multiprocessing.cpu_count()):
    if enable:
        global outputStates
        global outputFormatString
        outputStates = [""] * (threadCount)
        outputFormatString = ""
        for x in xrange(threadCount):
            outputFormatString = outputFormatString + "{" + str(x) + ":10}"

        sys.stdout = StdOutHook()
        sys.stderr = StdErrHook()
        __builtin__.print = threadedPrint
        sys.exit = threadedExit
    else:
        sys.stdout = __builtin__.org_stdout
        sys.stderr = __builtin__.org_sterr
        __builtin__.print = __builtin__.org_print
        sys.exit = __builtin__.org_exit

threadData = threading.local()

def nextProgressIndicator():
    return next(threadData.progressIndicator)

class TaskFunction():
    def __init__(self, function, *arguments):
        self.function = function
        self.arguments = arguments

class Task():
    def __init__(self, description, function = None, *arguments):
        self.taskNumber = 0 # will be set from outside
        self.description = description
        self.listOfFunctions = []
        if function:
            firstFunction = TaskFunction(function, *arguments)
            self.listOfFunctions.append(firstFunction)

    def addFunction(self, function, *arguments):
        aFunction = TaskFunction(function, *arguments)
        self.listOfFunctions.append(aFunction)

    def do(self, outputSlot = None, maxOutputSlot = None):
        for taskFunction in self.listOfFunctions:
            taskFunction.function(*(taskFunction.arguments))
        print("Done")

class ThreadedWork():
    def __init__(self, description):
        self.description = "##### {} #####".format(description)
        self.queue = queue.Queue()
        self.legend = []
        self.taskNumber = 0

    def addTask(self, description, function, *arguments):
        self.addTaskObject(Task(description, function, *arguments))

    def addTaskObject(self, task):
        task.taskNumber = self.taskNumber
        self.legend.append(("{:d}: " + os.linesep +"\t{}" + os.linesep).format(task.taskNumber, task.description))
        self.queue.put(task)
        self.taskNumber = self.taskNumber + 1

    def run(self, maxThreads = multiprocessing.cpu_count()):
        print(self.description)
        print(os.linesep.join(self.legend))

        #enableThreadedPrint(True, maxThreads)
        listOfConsumers = []
        for i in range(maxThreads):
            # every Consumer needs a stop/none item
            self.queue.put(None)
            newConsumer = Consumer(self.queue, i)
            listOfConsumers.append(newConsumer)
            newConsumer.daemon = True
            newConsumer.start()

        # block until everything is done
        for consumer in listOfConsumers:
            while consumer.isAlive():
                try:
                    #wait 1 second, then go back and ask if thread is still alive
                    time.sleep(1)
                except KeyboardInterrupt: #if ctrl-C is pressed within that second,
                    #catch the KeyboardInterrupt exception
                    sys.exit(0)
        # self.queue.join() <- this ignoring the KeyboardInterrupt
        #enableThreadedPrint(False)
        print(os.linesep + self.description + ' ... done')

class Consumer(threading.Thread):
    def __init__(self, queue, workerThreadId):
        self.queue = queue
        self.workerThreadId = workerThreadId
        threading.Thread.__init__(self)
    def run(self):
        threadData.progressIndicator = itertools.cycle(['|', '/', '-', '\\'])
        threadData.workerThreadId = self.workerThreadId
        # run as long we have something in that queue
        while True:
            task = self.queue.get()
            if task is None:
                self.queue.task_done()
                break
            else:
                # we like to know which task get the progress -> see std handling
                threadData.taskNumber = task.taskNumber
                task.do()
                self.queue.task_done()