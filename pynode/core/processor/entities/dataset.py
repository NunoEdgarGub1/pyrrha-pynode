import h5py
import logging
import numpy as np

from core.manager import Manager
from core.patterns.pynode_logger import LogSocketHandler


class Dataset:

    def __init__(self, dataset_file, ipfs_api, batch_no: int):
        # Initializing logger object
        self.logger = logging.getLogger("Kernel")
        self.logger.addHandler(LogSocketHandler.get_instance())
        self.manager = Manager.get_instance()

        self.json_dataset = dataset_file
        # variable for determinate process (predict, fit)
        self.process = None

        # variables for predict job by batches
        self.data_address = None
        self.batch_no = batch_no
        self.dataset = None

        # variables for training (fit)
        self.train_x_address = None
        self.train_x_dataset = None
        self.train_y_address = None
        self.train_y_dataset = None
        self.loss = None
        self.optimizer = None
        self.batch_size = None
        self.epochs = None
        self.validation_split = 0
        self.shuffle = False
        self.initial_epoch = 0

        self.ipfs_api = ipfs_api

    def init_dataset(self):
        # parse all incoming dataset data
        train_block = False
        batches_block = False
        try:
            # train block parsing
            train_block = self.json_dataset['train']
            self.train_x_address = train_block['train_x']
            self.train_y_address = train_block['train_y']
        except Exception as ex:
            self.logger.error("Wrong Dataset data file structure")
            self.logger.error(ex.args)

        try:
            # options block parsing
            options_block = self.json_dataset['options']
            # --------- are necessary for model compilation
            self.loss = options_block['loss']
            self.optimizer = options_block['optimizer']
            # ---------------------------------------------
            self.batch_size = options_block['batch_size']
            self.epochs = options_block['epochs']
            self.validation_split = options_block['validation_split']
            self.shuffle = options_block['shuffle']
            self.initial_epoch = options_block['initial_epoch']
            train_block = True
        except Exception as ex:
            self.logger.error("Wrong Dataset data file structure")
            self.logger.error(ex.args)

        if train_block is False:
            try:
                # batches block parsing (only for prediction)
                batches = self.json_dataset['batches']
                self.data_address = batches[self.batch_no]
                batches_block = True
            except Exception as ex:
                self.logger.error("Wrong Dataset data file structure")
                self.logger.error(ex.args)

        if train_block is False and batches_block is False:
            self.logger.error('Unable to parse train or batches block')
            return False

        # try to get train_x dataset
        if self.train_x_address:
            try:
                self.logger.info("Downloading train_x file %s", self.train_x_address)
                self.ipfs_api.download_file(self.train_x_address)
            except Exception as ex:
                self.logger.error("Can't download data file from IPFS: %s", type(ex))
                self.logger.error(ex.args)
                return False

        # try to get train_y dataset
        if self.train_y_address:
            try:
                self.logger.info("Downloading train_y file %s", self.train_y_address)
                self.ipfs_api.download_file(self.train_y_address)
            except Exception as ex:
                self.logger.error("Can't download data file from IPFS: %s", type(ex))
                self.logger.error(ex.args)
                return False

        # try to get dataset for prediction
        if self.data_address:
            try:
                self.logger.info("Downloading data file %s", self.data_address)
                self.ipfs_api.download_file(self.data_address)
            except Exception as ex:
                self.logger.error("Can't download data file from IPFS: %s", type(ex))
                self.logger.error(ex.args)
                return False

        # check dataset params and set working mode
        if self.train_x_address and self.train_y_address:
            self.logger.info("Set computing mode to training")
            self.process = 'fit'
        else:
            self.logger.info("Set computing mode to prediction")
            self.process = 'predict'

        return True

    def read_dataset(self) -> np.ndarray:
        if self.dataset is not None:
            return self.dataset

        self.logger.info('Loading dataset...')
        h5f = h5py.File(self.data_address, 'r')
        # magic internal variable can not be empty (for more easy performance named as structure variable)
        h5ds = h5f['batches']
        self.dataset = np.ndarray(shape=h5ds.shape)
        h5ds.read_direct(dest=self.dataset)
        return self.dataset

    def read_x_train_dataset(self) -> np.ndarray:
        if self.train_x_dataset is not None:
            return self.train_x_dataset

        self.logger.info('Loading train_x dataset...')
        h5f = h5py.File(self.train_x_address, 'r')
        # magic internal variable can not be empty (for more easy performance named as structure variable)
        h5ds = h5f['train_x']
        self.train_x_dataset = np.ndarray(shape=h5ds.shape)
        h5ds.read_direct(dest=self.train_x_dataset)
        return self.train_x_dataset

    def read_y_train_dataset(self) -> np.ndarray:
        if self.train_y_dataset is not None:
            return self.train_y_dataset

        self.logger.info('Loading train_y dataset...')
        h5f = h5py.File(self.train_y_address, 'r')
        # magic internal variable can not be empty (for more easy performance named as structure variable)
        h5ds = h5f['train_y']
        self.train_y_dataset = np.ndarray(shape=h5ds.shape)
        h5ds.read_direct(dest=self.train_y_dataset)
        return self.train_y_dataset


