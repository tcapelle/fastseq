# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/11_nbeats.metrics.ipynb (unless otherwise specified).

__all__ = ['NBeatsTheta', 'NBeatsBackwards', 'NBeatsAttention', 'NBeatsTheta', 'nbeats_learner']

# Cell
from fastcore.utils import *
from fastcore.imports import *
from fastai2.basics import *
from fastai2.callback.hook import num_features_model
from fastai2.callback.all import *
from fastai2.torch_core import *
from torch.autograd import Variable
from ..all import *

from .model import *

# Cell
def _get_key_from_nested_dct(dct, s_key, exclude = [], namespace=''):
    r = {}
    for key in dct.keys():
        if sum([exc in key for exc in exclude])== 0 :
            if type(dct[key]) == dict:
                r.update(_get_key_from_nested_dct(dct[key], s_key, exclude, namespace=namespace+key))
            if s_key in key:
                r[namespace+key] = dct[key]
    return r

# Cell
class NBeatsTheta(Metric):
    "The sqaure of the `theta` for every block. "
    def reset(self):           self.total,self.count = 0.,0
    def accumulate(self, learn):
        bs = find_bs(learn.yb)
        theta_dct = _get_key_from_nested_dct(learn.n_beats_trainer.out,'theta',['bias','total','att'])
        t = torch.cat([v.float() for k,v in theta_dct.items()])
        self.total += to_detach(t.abs().mean())*bs
        self.count += bs
    @property
    def value(self): return self.total/self.count if self.count != 0 else None
    @property
    def name(self):  return "theta"

# Cell
class NBeatsBackwards(Metric):
    "The loss according to the `loss_func` on the backwards part of the time-serie."
    def reset(self):           self.total,self.count = 0.,0
    def accumulate(self, learn):
        bs = find_bs(learn.yb)
        b = learn.n_beats_trainer.out['total_b']
        value = learn.loss_func(b.float(), *learn.xb, reduction='mean')
        self.total += to_detach(value)*bs
        self.count += bs
    @property
    def value(self): return self.total/self.count if self.count != 0 else None
    @property
    def name(self):  return "b_loss"

# Cell
class NBeatsAttention(Callback):
    def att(self,df=True):
        dct = {}
        for k,v in learn.n_beats_trainer.out.items():
            if isinstance(k,str):
                if 'seaonality' in k or 'trend' in k:
                    dct[k]={'att_mean':v['attention'].mean().cpu().numpy(),
                            'att_std':v['attention'].std().cpu().numpy()}
        if df:
            return pd.DataFrame(dct)
        return dct

# Cell
class NBeatsTheta(Callback):
    def means(self, df=True):
        theta_means = {k.replace('theta',''):v.float().cpu().data for k,v in _get_key_from_nested_dct(learn.n_beats_trainer.out,'theta',['total']).items()}
        ret = {}
        for k,v in theta_means.items():
            ret[k] = {}
            for i in range(v.shape[-1]):
                ret[k].update({'theta_'+str(i)+'_mean': v[:,i].mean().numpy(),
                               'theta_'+str(i)+'_std': v[:,i].std().numpy(),
                              })

#         ret = {k+'_theta_'+str(i):v }
        att = {k.replace('attention','att_mean'):v.mean().float().cpu().numpy() for k,v in _get_key_from_nested_dct(learn.n_beats_trainer.out,'att',['total']).items()}
        for k in ret.keys():
            for att_key in att.keys():
                if k in att_key:
                    ret[k].update({'att_mean':att[att_key]})

        if df:
            return pd.DataFrame(ret)
        return ret

# Cell
# from fastai2.basics import *
# from fastseq.all import *

@delegates(NBeatsNet.__init__)
def nbeats_learner(dbunch:TSDataLoaders, output_channels=None, metrics=None,cbs=None, theta=0., b_loss=0., loss_func=None, **kwargs):
    "Build a N-Beats style learner"
    model = NBeatsNet(
        device = dbunch.train.device,
        horizon = dbunch.train.horizon,
        lookback = dbunch.train.lookback,
        **kwargs
       )

    loss_func = ifnone(loss_func, CombinedLoss(F.mse_loss, smape, ratio = {'smape':.0005}))
    learn = Learner(dbunch, model, loss_func=loss_func, opt_func= Adam,
                    metrics=L(metrics)+L(mae, smape, F.mse_loss, NBeatsTheta(), NBeatsBackwards()),
                    cbs=L(NBeatsTrainer(theta, b_loss))+L(cbs)
                   )
    learn.lh = (dbunch.train.lookback/dbunch.train.horizon)
    return learn