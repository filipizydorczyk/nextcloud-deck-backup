"""
Based on https://gist.github.com/svbergerem/5914d7f87764901aefddba125af99938.
"""
from progress.bar import Bar
import requests
import urllib3

headers = {'OCS-APIRequest': 'true', 'Content-Type': 'application/json'}
requests.packages.urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning)


class ProgressListener:

    def __init__(self) -> None:
        self.__bar = None

    def update(self, total: int) -> None:
        if(self.__bar == None):
            self.__bar = Bar('Writing boards to nextcloud', max=total)
        else:
            self.__bar.next()

    def finishBar(self) -> None:
        if(self.__bar != None):
            self.__bar.finish()


class ProgressObserver:

    def __init__(self) -> None:
        self.__listeners = []
        self._warnings = []

    def addListener(self, listener: ProgressListener) -> None:
        self.__listeners.append(listener)

    def update(self, total: int) -> None:
        for listener in self.__listeners:
            listener.update(total)

    def getAllWaringns(self) -> list:
        result = self._warnings.copy()
        self._warnings = []
        return result


class DeckDownloader(ProgressObserver):

    def __init__(self, urlFrom: str, authFrom: tuple) -> None:
        super(DeckDownloader, self).__init__()
        self.__urlFrom = urlFrom
        self.__authFrom = authFrom

    def __getBoards(self):
        response = requests.get(
            f'{self.__urlFrom}/index.php/apps/deck/api/v1.0/boards',
            auth=self.__authFrom,
            headers=headers,
            verify=False)
        response.raise_for_status()
        return response.json()

    def __getBoardDetails(self, boardId):
        response = requests.get(
            f'{self.__urlFrom}/index.php/apps/deck/api/v1.0/boards/{boardId}',
            auth=self.__authFrom,
            headers=headers, verify=False)
        response.raise_for_status()
        return response.json()

    def __getStacks(self, boardId):
        response = requests.get(
            f'{self.__urlFrom}/index.php/apps/deck/api/v1.0/boards/{boardId}/stacks',
            auth=self.__authFrom,
            headers=headers, verify=False)
        response.raise_for_status()
        return response.json()

    def __getStacksArchived(self, boardId):
        response = requests.get(
            f'{self.__urlFrom}/index.php/apps/deck/api/v1.0/boards/{boardId}/stacks/archived',
            auth=self.__authFrom,
            headers=headers, verify=False)
        response.raise_for_status()
        return response.json()

    def fetchBoards(self):
        boards = self.__getBoards()
        totalJobAmount = len(boards)
        self.update(totalJobAmount)

        for board in boards:
            self.update(totalJobAmount)

            boardDetails = self.__getBoardDetails(board['id'])
            board['details'] = boardDetails

            stacks = self.__getStacks(board['id'])
            board['stacks'] = stacks

            stacks = self.__getStacksArchived(board['id'])
            board['archived'] = stacks

        return boards


class DeckSender(ProgressObserver):

    def __init__(self, urlTo: str, authTo: tuple) -> None:
        super(DeckSender, self).__init__()
        self.__urlTo = urlTo
        self.__authTo = authTo

    def __createBoard(self, title, color):
        response = requests.post(
            f'{self.__urlTo}/index.php/apps/deck/api/v1.0/boards',
            auth=self.__authTo,
            json={
                'title': title,
                'color': color
            },
            headers=headers, verify=False)
        response.raise_for_status()
        board = response.json()
        boardId = board['id']
        # remove all default labels
        for label in board['labels']:
            labelId = label['id']
            response = requests.delete(
                f'{self.__urlTo}/index.php/apps/deck/api/v1.0/boards/{boardId}/labels/{labelId}',
                auth=self.__authTo,
                headers=headers)
            response.raise_for_status()
        return board

    def __createLabel(self, title, color, boardId):
        response = requests.post(
            f'{self.__urlTo}/index.php/apps/deck/api/v1.0/boards/{boardId}/labels',
            auth=self.__authTo,
            json={
                'title': title,
                'color': color
            },
            headers=headers, verify=False)
        response.raise_for_status()
        return response.json()

    def __createStack(self, title, order, boardId):
        response = requests.post(
            f'{self.__urlTo}/index.php/apps/deck/api/v1.0/boards/{boardId}/stacks',
            auth=self.__authTo,
            json={
                'title': title,
                'order': order
            },
            headers=headers, verify=False)
        response.raise_for_status()
        return response.json()

    def __createCard(self, title, ctype, order, description, duedate, boardId, stackId):
        response = requests.post(
            f'{self.__urlTo}/index.php/apps/deck/api/v1.0/boards/{boardId}/stacks/{stackId}/cards',
            auth=self.__authTo,
            json={
                'title': title,
                'type': ctype,
                'order': order,
                'description': description,
                'duedate': duedate
            },
            headers=headers, verify=False)
        response.raise_for_status()
        return response.json()

    def __assignLabel(self, labelId, cardId, boardId, stackId):
        response = requests.put(
            f'{self.__urlTo}/index.php/apps/deck/api/v1.0/boards/{boardId}/stacks/{stackId}/cards/{cardId}/assignLabel',
            auth=self.__authTo,
            json={
                'labelId': labelId
            },
            headers=headers, verify=False)
        response.raise_for_status()

    def __archiveCard(self, card, boardId, stackId):
        cardId = card['id']
        card['archived'] = True
        response = requests.put(
            f'{self.__urlTo}/index.php/apps/deck/api/v1.0/boards/{boardId}/stacks/{stackId}/cards/{cardId}',
            auth=self.__authTo,
            json=card,
            headers=headers, verify=False)
        response.raise_for_status()

    def __copyCard(self, card, boardIdTo, stackIdTo, labelsMap):
        createdCard = self.__createCard(
            card['title'],
            card['type'],
            card['order'],
            card['description'],
            card['duedate'],
            boardIdTo,
            stackIdTo
        )

        if card['labels']:
            for label in card['labels']:
                if (label['id'] in labelsMap):
                    self.__assignLabel(labelsMap[label['id']],
                                       createdCard['id'], boardIdTo, stackIdTo)
                else:
                    self._warnings.append("\nWARNING: Label with id {} skipped for {} card".format(
                        label['id'], card['title']))

        if card['archived']:
            self.__archiveCard(createdCard, boardIdTo, stackIdTo)

    def sendBoard(self, boards):
        totalJobAmount = len(boards)
        self.update(totalJobAmount)

        for board in boards:
            createdBoard = self.__createBoard(board['title'], board['color'])
            self.update(totalJobAmount)

            totalJobAmount = len(board['archived']) + \
                len(board['stacks']) + \
                len(board['details']['labels'])

            labelsMap = {}
            for label in board['details']['labels']:
                createdLabel = self.__createLabel(
                    label['title'], label['color'], createdBoard['id'])
                labelsMap[label['id']] = createdLabel['id']

            stacksMap = {}
            for stack in board['stacks']:
                createdStack = self.__createStack(
                    stack['title'], stack['order'], createdBoard['id'])
                stackIdTo = createdStack['id']
                stacksMap[stack['id']] = stackIdTo

                if not 'cards' in stack:
                    continue
                for card in stack['cards']:
                    self.__copyCard(
                        card, createdBoard['id'], stackIdTo, labelsMap)

            for stack in board['archived']:
                if not 'cards' in stack:
                    continue

                for card in stack['cards']:
                    self.__copyCard(card, createdBoard['id'],
                                    stacksMap[stack['id']], labelsMap)
