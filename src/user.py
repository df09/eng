import src.helpers.fo as fo
import src.helpers.pdo as pdo
from src.helpers.cmd import cmd

class User():
    def __init__(self, username):
        self.name = username
        self.path = f'data/users/{self.name}'
        self.f_data = f'{self.path}/_data.yml'
        self.f_progress_pronouns = f'{self.path}/progress.csv'
        self.data = fo.yml2dict(self.f_data)
        self.df_progress_pronouns = pdo.load(self.f_progress_pronouns)
        self.stats = self.get_stats()

    def get_stats(self):
        total,progress,a,b,c,d,f = self.data['stats']['pronouns'].values()
        return {'total':total,'progress':progress,'a':a,'b':b,'c':c,'d':d,'f':f}
