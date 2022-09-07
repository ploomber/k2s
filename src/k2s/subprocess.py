from subprocess import Popen, PIPE

from k2s.exceptions import CLIError


def _run_command(cmd):
    process = Popen(cmd, stdout=PIPE, stderr=PIPE)

    last_length = 0

    while True:
        output = process.stdout.readline().decode()

        if output == '' and process.poll() is not None:
            break

        if output:
            line = output.strip()
            print(' ' * last_length, end='\r')
            print(line, end='\r')
            last_length = len(line)

    print(' ' * last_length, end='\r')

    return_code = process.poll()

    # TODO: community link
    if return_code:
        print(f"ERRROR: {process.stderr.read().decode()}\n\n---")
        raise CLIError(process.stderr.read().decode())
