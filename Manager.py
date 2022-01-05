import subprocess
import pickle
from Torrent import Torrent

class FileManager:
    def __init__(self, sourceDir, destinationDir, creds, dbPath):
        self.sourceDir = sourceDir
        self.destinationDir = destinationDir
        self.creds = creds
        self.hashes = self.loadHashes(dbPath)
        self.dbPath = dbPath

    def loadHashes(self, dbPath):
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

    def saveHashes(self):
        f = open(self.dbPath, 'wb')
        pickle.dump(self.hashes, f)
        f.close()

    def getHashes(self, torrents):
        hashes = []
        ids = list(map(lambda torrent : torrent.getId(), torrents))
        ids = ','.join(ids)
        infoCmd = f'transmission-remote -n \'{self.creds}\' -t {ids} -i'
        infoOutput = subprocess.check_output(infoCmd, shell=True)
        info = infoOutput.decode('ASCII').split('Hash: ')
        for i in range(1, len(info)):
            torrentHash = info[i].split('\n')[0]
            hashes.append(torrentHash)
        return hashes

    def download(self, magnetLink):
        cmd = f'transmission-remote -n \'{self.creds}\' -a {magnetLink}'
        try:
            subprocess.check_output(cmd, shell=True)
            downloaded = self.getClientTorrents()[-1:]
            torrentHash = self.getHashes(downloaded)[-1]
            self.hashes.add(torrentHash)
            self.saveHashes()
            return True
        except subprocess.CalledProcessError as e:
            return False

    def transferCompletedTorrents(self):
        torrents = self.filterTorrents(self.getClientTorrents())
        if len(torrents) == 0: return
        completedTorrents = list(filter(lambda torrent : torrent.isDone(), torrents))
        if len(completedTorrents) == 0: return
        completedPaths = list(map(lambda torrent : torrent.getPath(), completedTorrents))
        completedPaths = ' '.join(completedPaths)
        cmd = f'mv {completedPaths} {self.destinationDir}'
        subprocess.check_output(cmd, shell=True)

    def removeCompletedTorrents(self):
        torrents = self.filterTorrents(self.getClientTorrents())
        if len(torrents) == 0: return
        completedTorrents = list(filter(lambda torrent : torrent.isDone(), torrents))
        if len(completedTorrents) == 0: return
        completedHashes = set(self.getHashes(completedTorrents))
        self.hashes = self.hashes.difference(completedHashes)
        self.saveHashes()
        completedIds = list(map(lambda torrent : torrent.getId(), completedTorrents))
        completedIds = ','.join(completedIds)
        cmd = f'transmission-remote -n \'{self.creds}\' -t {completedIds} -r'
        subprocess.check_output(cmd, shell=True)

    def filterTorrents(self, torrents):
        if len(torrents) == 0: return torrents
        # filter by hash
        hashes = self.getHashes(torrents)
        for i in range(len(hashes)):
            if hashes[i] not in self.hashes:
                torrents.pop(i)
        return torrents

    def getClientTorrents(self):
        listCmd = f'transmission-remote -n \'{self.creds}\' -l'
        listOutput = subprocess.check_output(listCmd, shell=True)
        rows = listOutput.decode('ASCII').split('\n')
        torrents = []
        for rawData in rows[1:len(rows)-2]:
            torrent = Torrent(rawData, self.sourceDir)
            torrents.append(torrent)
        return torrents
