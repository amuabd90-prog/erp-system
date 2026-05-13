#!/usr/bin/env python3
"""
Amana ERP - Build Script
Creates a standalone executable using PyInstaller
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def check_requirements():
    """Check if required packages are installed"""
    required_packages = ['pyinstaller']
    missing_packages = []
    
    for package in required_packages:
        try:
            subprocess.run([sys.executable, '-c', f'import {package}'], 
                         check=True, capture_output=True)
        except subprocess.CalledProcessError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing_packages)

def create_app_icon():
    """Create app icon if it doesn't exist"""
    icon_path = Path('static/img/icon.ico')
    if not icon_path.exists():
        print("Creating default app icon...")
        # Create a simple icon directory
        icon_path.parent.mkdir(parents=True, exist_ok=True)
        
        # For now, we'll use a placeholder
        # In production, you should have a proper .ico file
        print("Note: Add a proper icon.ico file to static/img/ for professional appearance")
    
    return icon_path if icon_path.exists() else None

def clean_build_dirs():
    """Clean previous build directories"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"Cleaning {dir_name} directory...")
            shutil.rmtree(dir_path)

def create_spec_file():
    """Create PyInstaller spec file"""
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('instance', 'instance'),
    ],
    hiddenimports=[
        'flask',
        'flask_login',
        'sqlalchemy',
        'werkzeug.security',
        'flask_wtf',
        'email_validator',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='HABusinessManagementSystem',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='static/img/icon.ico' if os.path.exists('static/img/icon.ico') else None,
    description='Amana ERP - Complete ERP Solution',
    uac_admin=False,
    uac_uiaccess=False,
)
'''
    
    with open('AmanaERP.spec', 'w') as f:
        f.write(spec_content)
    
    return 'AmanaERP.spec'

def build_executable():
    """Build the executable using PyInstaller"""
    spec_file = create_spec_file()
    
    print("Building executable...")
    print(f"Using spec file: {spec_file}")
    
    # Build command
    cmd = [
        sys.executable, 
        '-m', 
        'PyInstaller',
        '--clean',
        '--noconfirm',
        spec_file
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Build completed successfully!")
        print(result.stdout)
        
        # Check if executable was created
        exe_path = Path('dist/HABusinessManagementSystem.exe')
        if exe_path.exists():
            print(f"✓ Executable created: {exe_path.absolute()}")
            print(f"Size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
        else:
            print("✗ Executable not found in dist/ directory")
            
    except subprocess.CalledProcessError as e:
        print(f"✗ Build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False
    
    return True

def create_installer_script():
    """Create Inno Setup installer script"""
    # Only create installer.iss if it doesn't exist
    if os.path.exists('installer.iss'):
        print("✓ installer.iss already exists - skipping creation")
        return
        
    installer_content = '''#define MyAppName "Amana ERP"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "H&A Solutions"
#define MyAppURL "http://localhost:5000"
#define MyAppExeName "HABusinessManagementSystem.exe" 

[Setup]
AppId={{A8E2F1D4-6B5C-4A3D-9E2F-1C8B7A6D5E4F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=installer
OutputBaseFilename=Amana_ERP_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "dist\\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "templates\\*"; DestDir: "{app}\\templates"; Flags: recursesubdirs createallsubdirs
Source: "static\\*"; DestDir: "{app}\\static"; Flags: recursesubdirs createallsubdirs
Source: "instance\\*"; DestDir: "{app}\\instance"; Flags: recursesubdirs createallsubdirs
Source: "README.md"; DestDir: "{app}"; Flags: isreadme
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: islicense

[Icons]
Name: "{group}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"
Name: "{group}\\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Registry]
Root: HKLM; Subkey: "Software\\HABusinessManagementSystem"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"
Root: HKLM; Subkey: "Software\\HABusinessManagementSystem"; ValueType: string; ValueName: "DisplayName"; ValueData: "H/A Business Management System"
Root: HKLM; Subkey: "Software\\HABusinessManagementSystem"; ValueType: string; ValueName: "Version"; ValueData: "1.0.0"
'''
    
    with open('installer.iss', 'w') as f:
        f.write(installer_content)
    
    print("✓ Inno Setup script created: installer.iss")

def create_license_file():
    """Create license file for installer"""
    license_content = '''Amana ERP License Agreement

Copyright (c) 2024 H/A Business Solutions

This software is licensed under the MIT License:

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
'''
    
    with open('LICENSE.txt', 'w') as f:
        f.write(license_content)
    
    print("✓ License file created: LICENSE.txt")

def create_readme():
    """Create README file"""
    readme_content = '''# Amana ERP

A comprehensive ERP solution for business management.

## Features

- Multi-user role-based access control
- Inventory management
- Sales tracking
- Expense management
- Financial reporting
- Ethiopian tax calculations
- Multi-company support
- Audit trail
- Data export functionality

## Installation

1. Run the installer (HABusinessManagementSystem_Setup.exe)
2. Follow the installation wizard
3. Launch the application from desktop shortcut or Start Menu

## Usage

1. Open your web browser
2. Navigate to http://localhost:5000
3. Login with your credentials
4. Access features based on your role

## Support

For technical support, contact:
- Email: support@example.com
- Phone: +2511234567

## System Requirements

- Windows 10 or higher
- 4GB RAM minimum
- 500MB disk space
- Modern web browser
'''
    
    with open('README.md', 'w') as f:
        f.write(readme_content)
    
    print("✓ README file created: README.md")

def main():
    """Main build function"""
    print("Amana ERP - Build Script")
    print("=" * 50)
    
    # Check current directory
    if not Path('app.py').exists():
        print("✗ Error: app.py not found in current directory")
        print("Please run this script from the project root directory")
        return
    
    # Check and install requirements
    check_requirements()
    
    # Create necessary files
    create_app_icon()
    create_license_file()
    create_readme()
    
    # Clean previous builds
    clean_build_dirs()
    
    # Build executable
    if build_executable():
        # Create installer script
        create_installer_script()
        
        print("\n" + "=" * 50)
        print("Build completed successfully!")
        print("\nNext steps:")
        print("1. Install Inno Setup (if not already installed)")
        print("2. Run: 'iscc installer.iss' to create installer")
        print("3. Find installer in 'installer' directory")
        print("\nExecutable location: dist/AmanaERP.exe")
    else:
        print("\n✗ Build failed. Please check the error messages above.")

if __name__ == "__main__":
    main()
