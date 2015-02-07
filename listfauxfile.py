
nl='\n'
class FILE:
  def __init__(self,ss=''): 
    self.lines = [s for s in ss.split(nl)]
    self.nlines = len(self.lines)
    self.dotell = 0

  def readline(self):
    if self.dotell>=self.nlines: return ''
    self.dotell += 1
    return self.lines[self.dotell-1] + nl

  def tell(self):
    return self.dotell
