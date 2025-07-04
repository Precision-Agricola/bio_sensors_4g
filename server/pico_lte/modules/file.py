"""
Module for including file functions of PicoLTE module.
"""

from pico_lte.utils.status import Status

class File:
    """
    Class for inculding functions of file operations of PicoLTE module.
    """

    CTRL_Z = "\x1A"

    def __init__(self, atcom):
        """
        Initialization of the class.
        """
        self.atcom = atcom

    def get_file_list(self, path="*"):
        """
        Function for getting file list

        Parameters
        ----------
        path : str, default: "*"
            Path to the directory

        Returns
        -------
        dict
            Result that includes "status" and "response" keys
        """
        command = f'AT+QFLST="{path}"'
        return self.atcom.send_at_comm(command)

    def delete_file_from_modem(self, file_name):
        """
        Function for deleting file from modem UFS storage

        Parameters
        ----------
        file_path : str
            Path to the file

        Returns
        -------
        dict
            Result that includes "status" and "response" keys
        """
        command = f'AT+QFDEL="{file_name}"'
        return self.atcom.send_at_comm(command)

    def upload_file_to_modem(self, filename, file, timeout=5000):
        """
        Function for uploading file to modem

        Parameters
        ----------
        file : str
            Path to the file
        timeout : int, default: 5000
            Timeout for the command

        Returns
        -------
        dict
            Result that includes "status" and "response" keys
        """
        len_file = len(file)
        command = f'AT+QFUPL="{filename}",{len_file},{timeout}'
        result = self.atcom.send_at_comm(command, "CONNECT", urc=True)

        if result["status"] == Status.SUCCESS:
            self.atcom.send_at_comm_once(file)  # send ca cert
            return self.atcom.send_at_comm(self.CTRL_Z)  # send end char -> CTRL_Z
        return result

    def download_file_from_modem(self, filename, timeout=10000):
        """
        Function for starting a file download from modem UFS storage.

        Parameters
        ----------
        filename : str
            Name in modem (e.g. "UFS:my.zip")
        timeout : int, default: 5000
            Timeout (ms) to wait for the CONNECT response

        Returns
        -------
        dict  { "status": Status.X, "response": ... }

        Notes
        -----
        * On SUCCESS the modem is now in data mode and will stream the file
          bytes over UART. Caller must read the binary stream and then the
          trailing "+QFDWL:" line and "OK".
        """
        import time
        self.atcom.send_at_comm_once(f'AT+QFDWL="{filename}"')

        uart  = self.atcom.modem_com
        buf   = b""
        t0    = time.ticks_ms()
        while b"CONNECT\r\n" not in buf:
            if uart.any():
                buf += uart.read(uart.any())
            elif time.ticks_diff(time.ticks_ms(), t0) > timeout:
                return {"status": Status.TIMEOUT, "response": "No CONNECT"}
            else:
                time.sleep_ms(5)

        return {"status": Status.SUCCESS, "response": "CONNECT"}
