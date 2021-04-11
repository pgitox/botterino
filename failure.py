from Botterino.hosterino import check
from config import pg
from Utils.utils import randomColor

# change these two lines as appropriate
answer = 31.492268, -9.764050      
tolerance = 20
manual = False 

submission = next(iter(pg.new())) 
check(submission, answer, tolerance)
print(f'{randomColor()}Checking answers on https://reddit.com{submission.permalink}')