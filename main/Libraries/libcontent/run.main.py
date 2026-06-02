import subprocess

def run(arg):
	command = arg.split(sep=" ")
	result = subprocess.run(command)
	return result.returncode

register_function("run", run)
