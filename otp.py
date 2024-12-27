import random
def genotp():
     otp=''
     a=[chr(i) for i in range(ord('A'),ord('Z')+1)]
     b=[chr(i) for i in range(ord('a'),ord('z')+1)]
     for i in range(2):
          otp=otp+random.choice(a)
          otp=otp+random.choice(b)
          otp=otp+str(random.randint(0,9))
     return otp