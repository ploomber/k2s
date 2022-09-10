class KernelRestartRequired(Exception):

    def __init__(self):
        msg = ("Successful conda installation, restarting kernel. "
               "Please re-run this cell to continue.")
        super().__init__(msg)


class CLIError(Exception):
    pass
