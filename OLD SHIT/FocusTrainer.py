#record today's date
#record the time right now
#allocate a session id (reset for today)
#task = input("What task are you working on?")
#task_type = input("Select the type of task:Planning/Admin/Coding/Research")
import time
run = input("Start? Y/N") #only run if user types Y
stop = input("Stop? Y/N")
mins = 0
if run == "Y":
    while stop != "Y":
        print mins
        time.sleep(60)
        mins = mins + 1

#start_time = #time when they selected start now
#end_time = #time when they pressed distracted/finished
#if distracted, ask
#distraction = input("What was the distraction?")
#
