import torch
import torch.nn as nn
import torch.nn.functional as F
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "../../")))

from algorithms.optimizer import SAM
from algorithms.BaseClientTrainer import BaseClientTrainer
from algorithms.optim_utils import *

__all__ = ["ClientTrainer"]


class ClientTrainer(BaseClientTrainer):
    def __init__(self, **kwargs):
        super(ClientTrainer, self).__init__(**kwargs)
        """
        ClientTrainer class contains local data and local-specific information.
        After local training, upload weights to the Server.
        """
        self.sam_optimizer = None
        self.rho = self.algo_params.rho
        self.adaptive = self.algo_params.adaptive
        self.perturb_head = self.algo_params.perturb_head
        self.perturb_body = self.algo_params.perturb_body

    def train(self):
        """Local training"""
        self._keep_global()

        self.model.train()
        self.model.to(self.device)

        local_size = self.datasize

        for _ in range(self.local_epochs):
            for data, targets in self.local_loaders["train"]:
                data, targets = data.to(self.device), targets.to(self.device)

                # first forward-backward pass
                enable_running_stats(self.model)

                if not self.perturb_head:
                    freeze_head(self.model)

                if not self.perturb_body:
                    freeze_body(self.model)

                output = self.model(data)
                loss = self.criterion(
                    output, targets
                )  # use this loss for any training statistics
                loss.backward()

                if not self.perturb_head:
                    zerograd_head(self.model)

                if not self.perturb_body:
                    zerograd_body(self.model)

                self.sam_optimizer.first_step(zero_grad=True)

                unfreeze(self.model)

                # second forward-backward pass
                disable_running_stats(self.model)
                self.criterion(
                    self.model(data), targets
                ).backward()  # make sure to do a full forward pass
                self.sam_optimizer.second_step(zero_grad=True)

        local_results = self._get_local_stats()

        return local_results, local_size

    def download_global(self, server_weights, server_optimizer):
        """Load model & Optimizer"""
        self.model.load_state_dict(server_weights)
        self.optimizer.load_state_dict(server_optimizer)
        self.sam_optimizer = self._get_sam_optimizer(self.optimizer)

    def _get_sam_optimizer(self, base_optimizer):
        optim_params = base_optimizer.state_dict()
        lr = optim_params["param_groups"][0]["lr"]
        momentum = optim_params["param_groups"][0]["momentum"]
        weight_decay = optim_params["param_groups"][0]["weight_decay"]
        sam_optimizer = SAM(
            self.model.parameters(),
            base_optimizer=torch.optim.SGD,
            rho=self.rho,
            adaptive=self.adaptive,
            lr=lr,
            momentum=momentum,
            weight_decay=weight_decay,
        )

        return sam_optimizer
