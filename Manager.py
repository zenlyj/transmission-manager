import subprocess
import pickle
from Torrent import Torrent

class FileManager:
    def __init__(self, sourceDir, destinationDir, creds, dbPath):
        self.__sourceDir = sourceDir
        self.__destinationDir = destinationDir
        self.__creds = creds
        self.__hashes = self.__loadHashes(dbPath)
        self.__dbPath = dbPath

    def __loadHashes(self, dbPath):
        f = None
        hashes = None
        try:
            f = open(dbPath, 'rb')
            hashes = pickle.load(f)
        except (pickle.PicklingError, EOFError):
            hashes = set()
        except FileNotFoundError:
            f = open(dbPath, 'xb')
            hashes = set()
        f.close()
        return hashes

    def __saveHashes(self):
        f = open(self.__dbPath, 'wb')
        pickle.dump(self.__hashes, f)
        f.close()

    def __getHashes(self, torrents):
        hashes = []
        ids = list(map(lambda torrent : torrent.getId(), torrents))
        ids = ','.join(ids)
        infoCmd = f'transmission-remote -n \'{self.__creds}\' -t {ids} -i'
        infoOutput = subprocess.check_output(infoCmd, shell=True)
        info = infoOutput.decode('ASCII').split('Hash: ')
        for i in range(1, len(info)):
            torrentHash = info[i].split('\n')[0]
            hashes.append(torrentHash)
        return hashes

    def download(self, magnetLink):
        cmd = f'transmission-remote -n \'{self.__creds}\' -a {magnetLink}'
        try:
            subprocess.check_output(cmd, shell=True)
            downloaded = self.__getClientTorrents()[-1:]
            torrentHash = self.__getHashes(downloaded)[-1]
            self.__hashes.add(torrentHash)
            self.__saveHashes()
            return True
        except subprocess.CalledProcessError as e:
            return False

    def transferCompletedTorrents(self):
        torrents = self.__filterTorrents(self.__getClientTorrents())
        if len(torrents) == 0: return
        completedTorrents = list(filter(lambda torrent : torrent.isDone(), torrents))
        if len(completedTorrents) == 0: return
        completedPaths = list(map(lambda torrent : torrent.getPath(), completedTorrents))
        completedPaths = ' '.join(completedPaths)
        cmd = f'mv {completedPaths} {self.__destinationDir}'
        subprocess.check_output(cmd, shell=True)

    def removeCompletedTorrents(self):
        torrents = self.__filterTorrents(self.__getClientTorrents())
        if len(torrents) == 0: return
        completedTorrents = list(filter(lambda torrent : torrent.isDone(), torrents))
        if len(completedTorrents) == 0: return
        completedHashes = set(self.__getHashes(completedTorrents))
        self.__hashes = self.__hashes.difference(completedHashes)
        self.__saveHashes()
        completedIds = list(map(lambda torrent : torrent.getId(), completedTorrents))
        completedIds = ','.join(completedIds)
        cmd = f'transmission-remote -n \'{self.__creds}\' -t {completedIds} -r'
        subprocess.check_output(cmd, shell=True)

    def __filterTorrents(self, torrents):
        if len(torrents) == 0: return torrents
        # filter by hash
        hashes = self.__getHashes(torrents)
        for i in range(len(hashes)):
            if hashes[i] not in self.__hashes:
                torrents.pop(i)
        return torrents

    def __getClientTorrents(self):
        listCmd = f'transmission-remote -n \'{self.__creds}\' -l'
        listOutput = subprocess.check_output(listCmd, shell=True)
        rows = listOutput.decode('ASCII').split('\n')
        torrents = []
        for rawData in rows[1:len(rows)-2]:
            torrent = Torrent(rawData, self.__sourceDir)
            torrents.append(torrent)
        return torrents
