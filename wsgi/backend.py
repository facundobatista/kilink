'''

para usar:

import backend
backend.create_user('Nico Cesar','nico@nicocesar.com')
backend.create_kilink(1, 'import mindread')
backend.create_kilink(1, 'import this', 'sdkjj')
list(backend.get_kilink('sdkjj'))
backend.get_content('sdkjj',1)
backend.update_kilink('sdkjj', revno=1, user_id=2, content='keep it up')
list(backend.get_user_kilinks(1))
for a in backend.get_diff('sdkjj',1,2):
  print a 

'''
import sqlobject
import datetime
import difflib
import os
import uuid

db_filename = os.path.abspath('data.db')
if os.path.exists(db_filename):
    firsttime = False
else:
    firsttime = True

connection_string = 'sqlite:' + db_filename
#connection ='sqlite:/:memory:?debug=1'
connection = sqlobject.connectionForURI(connection_string)
sqlobject.sqlhub.processConnection = connection


##
## Sacado de: http://stackoverflow.com/questions/1119722

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

def base62_encode(num, alphabet=ALPHABET):
    """Encode a number in Base X

    `num`: The number to encode
    `alphabet`: The alphabet to use for encoding
    """
    if (num == 0):
        return alphabet[0]
    arr = []
    base = len(alphabet)
    while num:
        rem = num % base
        num = num // base
        arr.append(alphabet[rem])
    arr.reverse()
    return ''.join(arr)

def base62_decode(string, alphabet=ALPHABET):
    """Decode a Base X encoded string into the number

    Arguments:
    - `string`: The encoded string
    - `alphabet`: The alphabet to use for encoding
    """
    base = len(alphabet)
    strlen = len(string)
    num = 0
    idx = 0
    for char in string:
        power = (strlen - (idx + 1))
        num += alphabet.index(char) * (base ** power)
        idx += 1
    return num



class UserError:
    pass

class WrongTimestamp:
    def __init__(self, d):
        self.d=d

    def __repr__(self):
        return "wrong datetime: %s. Should be a datetime.datetime instance" % str(self.d)

class MissingKilink:
    def __init__(self, kid, revno):
        self.kid = kid
        self.revno = revno

    def __repr__(self):
        return "Missing kilink for kid = %s. and revno = %s" % (str(self.kid), str(self.revno))

class MultipleKilink:
    def __init__(self, kid, revno):
        self.kid = kid
        self.revno = revno

    def __repr__(self):
        return "Multiple kilink for kid = %s. and revno = %s. This shouldn't happen ever!" % (str(self.kid), str(self.revno))

class ExistingKilink:
    def __init__(self, kid):
        self.kid = kid

    def __repr__(self):
        return "There is already kilink for kid = %s" % str(self.kid)

class KiUser(sqlobject.SQLObject):
    name = sqlobject.UnicodeCol()
    email = sqlobject.StringCol()

class Kilink(sqlobject.SQLObject):
    kid = sqlobject.StringCol()
    revno = sqlobject.IntCol()
    parent_revno = sqlobject.IntCol()
    user = sqlobject.ForeignKey('KiUser')
    content = sqlobject.PickleCol() ## in the future we can store preprocessed HTML objects
    timestamp  = sqlobject.DateTimeCol()


def create_user(name, email):
    p = KiUser(name = name, email = email)
    return p.id

def create_kilink(user, content, kid=None, timestamp=None):

    if not kid:
        kid = base62_encode(int(uuid.uuid4()))

    results = Kilink.selectBy(kid=kid)
    if results.count() > 0:
        raise ExistingKilink(kid)
    

    try:
        u = KiUser.get(user)
    except Exception,e:
        raise UserError
    
    if not timestamp:
        timestamp = datetime.datetime.now()
    else:
        if not isinstance(timestamp,datetime.datetime):
            raise WrongTimestap(datetime)


    k = Kilink(kid = kid, revno=1, parent_revno=-1, user=u, content=content, timestamp=timestamp)
    return "ok "+ str(k.kid)

def get_kilink(kid):
    k = Kilink.selectBy(kid=kid)
    #FIXME: This will return an array of unique (kid, revno,... ) objects.
    ## there needs to be a done a more tree-like structure for this
    return k

def get_new_revno(kid):
    k = Kilink.selectBy(kid=kid).max(Kilink.q.revno)
    ## NOTE: This will bring a race condition... remember this is just a
    ## prototype, get_new_revno() should be reimplemented on 
    ## your favorite scale framework
    return int(k) + 1    

def update_kilink(kid, revno, user_id, content='', timestamp=None):
    u = None
    if user_id:
        try:
            u = KiUser.get(user_id)
        except Exception,e:
            raise UserError

    if revno:
        ## TODO:check if revno exists
        pass


    if not timestamp:
        timestamp = datetime.datetime.now()
    else:
        timestamp = timestamp

    k = Kilink(kid = kid, revno=get_new_revno(kid), parent_revno=revno, user=u, content=content, timestamp=timestamp)

    return "ok "+ str(k.kid)

def get_content(kid, revno=None):
    if not revno:
        revno = "1"
    results = Kilink.selectBy(kid=kid, revno=revno)
    if results.count() == 0:
        raise MissingKilink(kid, revno)
    elif results.count() > 1:
        raise MultipleKilink(kid, revno)

    return results[0].content

def get_diff(kid, revno1, revno2):
    kilink1 = get_content(kid, revno1).split("\n")
    kilink2 = get_content(kid, revno2).split("\n")
    return difflib.context_diff(kilink1, kilink2, fromfile='revision %d' % revno1, tofile='revision %d ' % revno2, lineterm="")

def get_user_kilinks(user_id):
    if user_id:
        try:
            u = KiUser.get(user_id)
        except Exception,e:
            raise UserError

    kilink_list = Kilink.selectBy(user = u)
    return kilink_list


if firsttime:
    KiUser.createTable()
    Kilink.createTable()
