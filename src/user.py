import src.helpers.fo as fo
import src.helpers.pdo as pdo
import src.helpers.colors as c
from src.helpers.cmd import cmd

class User():
    def __init__(self, username):
        self.name = username
        self.path = f'data/users/{self.name}'
        self.f_data = f'{self.path}/_data.yml'
        self.f_progress_pronouns = f'{self.path}/progress_pronouns.csv'
        self.data = fo.yml2dict(self.f_data)
        self.df_progress_pronouns = pdo.load(self.f_progress_pronouns)

    #   ┌─ df09 ──────┐
    # ┌─┴─ pronouns ──┴─────────────────────────────────────────────────────────┐
    # │ F:26 D:0 C:0 B:0 A:0                                     progress/total │
    # │ ####################################################################### │
    # └─────────────────────────────────────────────────────────────────────────┘
    def render_stats_pronouns(self):
        total,progress,a,b,c_est,d,f = self.data['stats']['pronouns'].values()
        # bar
        total_bar_length = 70
        if total == 0:
            scale = total_bar_length
        else:
            scale = total_bar_length / total
        f_length = round(f * scale)
        d_length = round(d * scale)
        c_length = round(c_est * scale)
        b_length = round(b * scale)
        a_length = round(a * scale)
        progress_length = f_length + d_length + c_length + b_length + a_length
        gray_length = total_bar_length - progress_length
        bar = ''
        bar += '[c]'+'#'*a_length
        bar += '[b]'+'#'*b_length
        bar += '[g]'+'#'*c_length
        bar += '[y]'+'#'*d_length
        bar += '[r]'+'#'*f_length
        bar += '[x]'+'#'*gray_length
        estimations = f'[c]A:{a} [b]B:{b} [g]C:{c_est} [y]D:{d} [r]F:{f}'.ljust(44)
        summary = f'[x]{progress}/{total}'.rjust(10)
        # render
        c.p(f'[x]    ┌─ [y]{self.name}[x] ──────┐')
        c.p(f'[x]┌─┴─ pronouns ──┴────────────────────────────────────────────────────────┐')
        c.p(f'[x]│ {estimations}                                    {summary} │')
        c.p(f'[x]│ {bar} │')
        c.p(f'[x]└────────────────────────────────────────────────────────────────────────┘')
        # return
        return f'[x]  ┌─ [y]{self.name}[x] ──────┐\n'+\
               f'[x]┌─┴─ pronouns ──┴────────────────────────────────────────────────────────┐\n'+\
               f'[x]│ {estimations}                                    {summary} │\n'+\
               f'[x]│ {bar} │\n'+\
               f'[x]└─────────────────────────────────────────────────────────────────────\n'
