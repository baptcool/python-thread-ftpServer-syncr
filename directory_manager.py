import logging
import os
import time
from Directory import Directory
from File import File
from talk_to_ftp import TalkToFTP
import subprocess
import queue
import threading
from logger import Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


class DirectoryManager:
    def __init__(self, ftp_website, directory, depth, excluded_extensions,  thread_enable,nb_thread ):
        self.root_directory = directory
        self.depth = depth
        self.arrayThr =  queue.Queue()

        if thread_enable == 1:
            if nb_thread >=1:
                self.nbThr = nb_thread
            else:
                self.nbThr = 1
        else:
            self.nbThr = 1


        Logger.log_info("number of threads : " + str(self.nbThr))
        self.nbThrInUse = 0


        self.lock = threading.Lock()
        self.excluded_extensions = excluded_extensions
        self.synchronize_dict = {}
        self.os_separator_count = len(directory.split(os.path.sep))
        self.paths_explored = []
        self.to_remove_from_dict = []
        self.ftp_website = ftp_website

        self.ftp = TalkToFTP(ftp_website)
        self.ftp.connect()
        if self.ftp.directory.count(os.path.sep) == 0:
            directory_split = ""
        else:
            directory_split = self.ftp.directory.rsplit(os.path.sep, 1)[0]
        if not self.ftp.if_exist(self.ftp.directory, self.ftp.get_folder_content(directory_split)):
            self.ftp.create_folder(self.ftp.directory)
        self.ftp.disconnect()



    def threadMain(self):
        while True != self.arrayThr.empty():
            temp = self.arrayThr.get()
            ftptemp =  TalkToFTP(self.ftp_website)
            ftptemp.connect()
            ftptemp.file_transfer(temp[0],temp[1],temp[2])
            ftptemp.disconnect()
            
        self.lock.acquire()
        try:
            self.nbThrInUse -= 1
        finally:
            self.lock.release()


    def manageThread(self):
        array = []
        if (self.nbThr - self.nbThrInUse >= 0 ):
            for i in range(self.nbThr - self.nbThrInUse):
                
                self.lock.acquire()
                try:
                    self.nbThrInUse += 1
                finally:
                    self.lock.release()
                array.append(threading.Thread(target = self.threadMain, args=[]))
            for e in array:
                e.start()
        
        
        
        


    def synchronize_directory(self, frequency):
        while True:
            self.paths_explored = []

            self.to_remove_from_dict = []

            self.ftp.connect()
            self.search_updates(self.root_directory)

            self.any_removals()
            self.ftp.disconnect()

            time.sleep(frequency)

    def search_updates(self, directory):
        for path_file, dirs, files in os.walk(directory):

            for dir_name in dirs:
                folder_path = os.path.join(path_file, dir_name)

                if self.is_superior_max_depth(folder_path) is False:
                    self.paths_explored.append(folder_path)


                    if folder_path not in self.synchronize_dict.keys():
                        self.synchronize_dict[folder_path] = Directory(folder_path)

                        split_path = folder_path.split(self.root_directory)
                        srv_full_path = '{}{}'.format(self.ftp.directory, split_path[1])
                        directory_split = srv_full_path.rsplit(os.path.sep,1)[0]
                        if not self.ftp.if_exist(srv_full_path, self.ftp.get_folder_content(directory_split)):
                            self.ftp.create_folder(srv_full_path)

            for file_name in files:
                file_path = os.path.join(path_file, file_name)

                
                if self.is_superior_max_depth(file_path) is False and \
                        (self.contain_excluded_extensions(file_path) is False):

                    self.paths_explored.append(file_path)
                    if file_path in self.synchronize_dict.keys():

                        if self.synchronize_dict[file_path].update_instance() == 1:
                            split_path = file_path.split(self.root_directory)
                            srv_full_path = '{}{}'.format(self.ftp.directory, split_path[1])
                            self.ftp.remove_file(srv_full_path)



                            self.arrayThr.put([path_file, srv_full_path, file_name])

                    else:

                        self.synchronize_dict[file_path] = File(file_path)
                        split_path = file_path.split(self.root_directory)
                        srv_full_path = '{}{}'.format(self.ftp.directory, split_path[1])
                       
                        self.arrayThr.put([path_file, srv_full_path, file_name])
        self.manageThread()



    def any_removals(self):
        
        if len(self.synchronize_dict.keys()) == len(self.paths_explored):
            return

        
        path_removed_list = [key for key in self.synchronize_dict.keys() if key not in self.paths_explored]

        for removed_path in path_removed_list:
            
            if removed_path not in self.to_remove_from_dict:
                
                if isinstance(self.synchronize_dict[removed_path], File):
                    split_path = removed_path.split(self.root_directory)
                    srv_full_path = '{}{}'.format(self.ftp.directory, split_path[1])
                    self.ftp.remove_file(srv_full_path)
                    self.to_remove_from_dict.append(removed_path)

                elif isinstance(self.synchronize_dict[removed_path], Directory):
                    split_path = removed_path.split(self.root_directory)
                    srv_full_path = '{}{}'.format(self.ftp.directory, split_path[1])
                    self.to_remove_from_dict.append(removed_path)
                    self.remove_all_in_directory(removed_path, srv_full_path, path_removed_list)

        
        for to_remove in self.to_remove_from_dict:
            if to_remove in self.synchronize_dict.keys():
                del self.synchronize_dict[to_remove]

    def remove_all_in_directory(self, removed_directory, srv_full_path, path_removed_list):
        directory_containers = {}
        for path in path_removed_list:

            
            if removed_directory != path and removed_directory in path \
                    and path not in self.to_remove_from_dict:

                
                if len(path.split(os.path.sep)) not in directory_containers.keys():
                    directory_containers[len(path.split(os.path.sep))] = [path]
                else:
                    
                    directory_containers[len(path.split(os.path.sep))].append(path)

        
        sorted_containers = sorted(directory_containers.values())

        
        for i in range(len(sorted_containers)-1, -1, -1):
            for to_delete in sorted_containers[i]:
                to_delete_ftp = "{0}{1}{2}".format(self.ftp.directory, os.path.sep, to_delete.split(self.root_directory)[1])
                if isinstance(self.synchronize_dict[to_delete], File):
                    self.ftp.remove_file(to_delete_ftp)
                    self.to_remove_from_dict.append(to_delete)
                else:
                    
                    self.remove_all_in_directory(to_delete, to_delete_ftp, path_removed_list)
        
        self.ftp.remove_folder(srv_full_path)
        self.to_remove_from_dict.append(removed_directory)

    
    def is_superior_max_depth(self, path):
        if (len(path.split(os.path.sep)) - self.os_separator_count) <= self.depth:
            return False
        else:
            return True

    def contain_excluded_extensions(self, file):
        extension = file.split(".")[1]
        if ".{0}".format(extension) in self.excluded_extensions:
            return True
        else:
            return False
