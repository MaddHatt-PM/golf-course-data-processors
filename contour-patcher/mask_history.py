import cv2 as cv


class MaskHistory:
    def __init__(self) -> None:
        self.__history = []
        self.__limit = 15

    def pushState(self, mat: cv.Mat) -> None:
        self.__history.append(mat)
        if len(self.__history) > self.__limit:
            print("dropped undo state")
            self.__history.pop(0)

    def canPopState(self) -> bool:
        return len(self.__history) != 0

    def popState(self) -> cv.Mat:
        return self.__history.pop()
