# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/06_models.dnn.ipynb (unless otherwise specified).

__all__ = ['DNN']

# Cell
from fastcore.utils import *
from fastcore.imports import *
from fastai2.basics import *
from fastai2.callback.hook import num_features_model

# Cell
class DNN(torch.nn.Module):
    """Implements a simple `DNN` architecture for time series forecasting. Inherits
    from pytorch `Module <https://pytorch.org/docs/stable/nn.html#torch.nn.Module>`_.

    Arguments:
        * input_channels (int): Number of covariates in input time series.
        * output_channels (int): Number of target time series.
        * horizon (int): Number of time steps to forecast.
        * lookback (int): Number of time steps to lookback.
        * hidden_channels (int): Number of channels in convolutional hidden layers.
        * p_dropout (float): Probality of dropout.
    """
    def __init__(self,
                 input_channels,
                 output_channels,
                 horizon,
                 lookback,
                 hidden_channels=64,
                 p_dropout=.2,
                ):
        """Inititalize variables."""
        super(DNN, self).__init__()
        self.output_channels = output_channels
        self.horizon = horizon
        self.hidden_channels = hidden_channels

        # Set up first layer for input
        ks = 3
        conv_input = torch.nn.Conv1d(
            in_channels=input_channels,
            out_channels=hidden_channels,
            kernel_size=ks,
            padding=(ks-1)//2
        )

        # Set up nonlinear output layers
        self.body = nn.Sequential(conv_input,Flatten())
        self.dnn = LinBnDrop((hidden_channels*lookback),horizon*output_channels)

    def forward(self, inputs):
        """Forward function."""
        hid = self.body(inputs.float())
        return self.dnn(hid).view(hid.size(0),self.output_channels,-1).float()

    @property
    def n_parameters(self):
        """Returns the number of model parameters."""
        par = list(self.parameters())
        s = sum([np.prod(list(d.size())) for d in par])
        return s