# Sand

**The Sand Interpreter** is a *very very very* lightweight programming language and interpreter written in Python.

It is pre-bundled with **notateOS** and **notation**, and is designed for creating applications, frameworks, libraries, and system components for notateOS.

## Features

- Simple syntax
- Can support Libraries written in Python
- Made using Python because I really don't know how to use other languages except Swift
- Support for libraries and frameworks
- Suitable for application development
- Extensible for future language features
- If I could describe it, I'd say C if it was more simpler + Python + Swift

## Installation time!!!

### Method 1: Download a Release

Download the latest release from the project's repository and follow the installation steps below.

### Method 2: Clone the git repo that you are currently at right now because yes :3

```bash
git clone https://github.com/astraiscorporations/sand.git sand
```

### Install Sand

Copy the Sand files to the system library directory:

```bash
sudo mkdir -p /usr/lib/sand
sudo cp -r sand/main/* /usr/lib/sand/
```

Create a symbolic link so Sand can be run from anywhere:

```bash
sudo ln -s /usr/lib/sand/main.py /usr/sbin/sand
```

You can now launch Sand with:

```bash
sand
```

## Usage

Sand can be used for:

- notateOS applications
- notateOS frameworks
- System utilities
- General scripting
- Library development

---

*Sand is developed as part of the notateOS by Astrais Corporations.*
*Written by Kankavee Tarnprasant. :)*
