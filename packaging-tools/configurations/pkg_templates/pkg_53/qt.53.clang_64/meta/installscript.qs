/*****************************************************************************
**
** Copyright (C) 2014 Digia Plc and/or its subsidiary(-ies).
** Contact: http://www.qt-project.org/legal
**
** This file is part of the release tools of the Qt Toolkit.
**
** $QT_BEGIN_LICENSE:LGPL$
** Commercial License Usage
** Licensees holding valid commercial Qt licenses may use this file in
** accordance with the commercial license agreement provided with the
** Software or, alternatively, in accordance with the terms contained in
** a written agreement between you and Digia.  For licensing terms and
** conditions see http://qt.digia.com/licensing.  For further information
** use the contact form at http://qt.digia.com/contact-us.
**
** GNU Lesser General Public License Usage
** Alternatively, this file may be used under the terms of the GNU Lesser
** General Public License version 2.1 as published by the Free Software
** Foundation and appearing in the file LICENSE.LGPL included in the
** packaging of this file.  Please review the following information to
** ensure the GNU Lesser General Public License version 2.1 requirements
** will be met: http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
**
** In addition, as a special exception, Digia gives you certain additional
** rights.  These rights are described in the Digia Qt LGPL Exception
** version 1.1, included in the file LGPL_EXCEPTION.txt in this package.
**
** GNU General Public License Usage
** Alternatively, this file may be used under the terms of the GNU
** General Public License version 3.0 as published by the Free Software
** Foundation and appearing in the file LICENSE.GPL included in the
** packaging of this file.  Please review the following information to
** ensure the GNU General Public License version 3.0 requirements will be
** met: http://www.gnu.org/copyleft/gpl.html.
**
**
** $QT_END_LICENSE$
**
*****************************************************************************/

// constructor
function Component()
{
    if (installer.value("os") == "mac") {
        var xcodeVersion = installer.execute("/usr/bin/xcodebuild", new Array("-version"))[0];
        if (xcodeVersion) {
            var version = xcodeVersion.replace( /\D+/g, '');
            if (parseInt(version) >= parseInt(400) && parseInt(version) <= parseInt(500)) {
                QMessageBox["warning"]("XcodeVersionError",
                        qsTr("You need to update Xcode to latest version!"),
                        qsTr("It is recommeneded to have Xcode version greater than 4.0.0 and smaller than 5.0.0 for Qt5.3 compilations with clang."));
            }
        }
        else {
            QMessageBox["warning"]("XcodeError",
                qsTr("Xcode installation not found!"),
                qsTr("You need to install Xcode version 5.0.0. Download Xcode from https://developer.apple.com/xcode\n"));
        }
    }
}

Component.prototype.beginInstallation = function()
{
    installer.setValue(component.name + "_qtpath", "@TargetDir@" + "%TARGET_INSTALL_DIR%");
}

Component.prototype.createOperations = function()
{
    component.createOperations();
    try {
        var qtStringVersion = "5.3";
        var qtPath = "@TargetDir@" + "%TARGET_INSTALL_DIR%";
        var qmakeBinary = "@TargetDir@" + "%TARGET_INSTALL_DIR%/bin/qmake";
        addInitQtPatchOperation(component, "mac", qtPath, qmakeBinary, "qt5");

        if (installer.value("SDKToolBinary") == "")
            return;

        component.addOperation("Execute",
                               ["@SDKToolBinary@", "addQt",
                                "--id", component.name,
                                "--name", "Qt " + qtStringVersion + " clang 64bit",
                                "--type", "Qt4ProjectManager.QtVersion.Desktop",
                                "--qmake", qmakeBinary,
                                "UNDOEXECUTE",
                                "@SDKToolBinary@", "rmQt", "--id", component.name]);

        var kitName = component.name + "_kit";
        component.addOperation("Execute",
                               ["@SDKToolBinary@", "addKit",
                                "--id", kitName,
                                "--name", "Desktop Qt " + qtStringVersion + " clang 64bit",
                                "--toolchain", "x86-macos-generic-mach_o-64bit",
                                "--qt", component.name,
                                "--debuggerengine", "1",
                                "--devicetype", "Desktop",
                                "UNDOEXECUTE",
                                "@SDKToolBinary@", "rmKit", "--id", kitName]);

        // patch/register docs and examples
        var installationPath = installer.value("TargetDir") + "%TARGET_INSTALL_DIR%";
        print("Register documentation and examples for: " + installationPath);
        patchQtExamplesAndDoc(component, installationPath, "Qt-5.3");

        //QTBUG-37650
        patchQtAssistant(component, installationPath, "Qt-5.3");

    } catch(e) {
        print(e);
    }
}

//QTBUG-37650
function patchQtAssistant(aComponent, aComponentRootPath, aQtInstallationName)
{
    if (installer.value("os") == "mac") {
        print("Patching qt.conf for Assistant to: " + aComponentRootPath);
        var fileName = aComponentRootPath + "/bin/Assistant.app/Contents/Resources/" + "qt.conf";
        print("qt.conf file: " + fileName);

        aComponent.addOperation("Settings",
            "path=" + fileName,
            "method=add_array_value",
            "key=Paths/Prefix",
            "value=../../..");

        aComponent.addOperation("Settings",
        "path=" + fileName,
        "method=add_array_value",
        "key=Paths/Documentation",
        "value=../../Docs/" + aQtInstallationName);
    }
}

