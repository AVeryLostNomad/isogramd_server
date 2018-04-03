

class ServerConfiguration:

    def __init__(self, isogram_server):
        windows_path = "C://Users//joeye//Documents//"
        mac_path = "/tmp/"
        server_ip = '45.20.80.26'
        local_ip = 'localhost'

        self.isogram_server = isogram_server

        self.ip = local_ip
        self.domain = self.ip + ":5000"
        self.file_base = windows_path + "isogram/"

    def get_domain(self):
        return self.domain