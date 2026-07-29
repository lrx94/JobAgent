from abc import ABC, abstractmethod

class JobProvider(ABC):

    @abstractmethod
    def search(self, keyword: str, location: str):
        pass