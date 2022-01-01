class Torrent:
    def __init__(self, rawData, sourceDir):
        self.rawData = rawData
        self.sourceDir = sourceDir
        self.parseData(rawData)

    def parseData(self, rawData):
        split = rawData.split()
        self.torrentId = split[0]
        self.donePercentage = split[1]
        self.have = split[2] + split[3]
        self.eta = split[4]
        self.upSpeed = split[5]
        self.downSpeed = split[6]
        self.ratio = split[7]
        self.status = split[8]
        self.name = ' '.join(split[9:])

    def getId(self):
        return self.torrentId

    def isDone(self):
        return self.donePercentage == '100%' and self.eta == 'Done'

    def getPath(self):
        return self.sourceDir + "'" + self.name + "'"