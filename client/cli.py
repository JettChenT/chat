from executer import Executer
import atexit

exc = Executer(("202.182.119.187", 6000))
atexit.register(exc.on_exit)
while True:
    inp = input("enter your command:\n")
    if inp == "bye":
        break
    ret = exc.exec_(inp)
    print(ret)