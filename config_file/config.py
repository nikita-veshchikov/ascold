
import yaml

class Configuration:

  def __init__(self, conf_file):
    self.conf_file = yaml.load(open(conf_file).read())

  def test_f(self):
    print (self.conf_file)

  def get_rand_list_of_addr(self):
    return self.conf_file['rand_list_of_addr']

  def get_rand_list_of_labels(self):
    return self.conf_file['rand_list_of_labels']

  def get_rand_list_of_regs(self):
    return self.conf_file['rand_list_of_regs']

  def get_mask_list_of_addr(self):
    return self.conf_file['mask_list_of_addr']

  def get_mask_list_of_labels(self):
    return self.conf_file['mask_list_of_labels']

  def get_mask_list_of_regs(self):
    return self.conf_file['mask_list_of_regs']

  def get_constants_list_of_addr(self):
    return self.conf_file['constants_list_of_addr']

  def get_constants_list_of_labels(self):
    return self.conf_file['constants_list_of_labels']

  def get_constants_list_of_regs(self):
    return self.conf_file['constants_list_of_regs']

  def get_label_addr_rng(self):
    return self.conf_file['rng']


if __name__ == "__main__":
  config_obj = Configuration("config_expl.yaml")

  print ("rand, list of addresses:", config_obj.get_rand_list_of_addr())
  print ("rand, list of labels:", config_obj.get_rand_list_of_labels())
  print ("rand, list of regs:", config_obj.get_rand_list_of_regs())

  print ("mask, list of addresses:", config_obj.get_mask_list_of_addr())
  print ("mask, list of labels:", config_obj.get_mask_list_of_labels())
  print ("mask, list of regs:", config_obj.get_mask_list_of_regs())

  print ("constants, list of addresses:", config_obj.get_constants_list_of_addr())
  print ("constants, list of labels:", config_obj.get_constants_list_of_labels())
  print ("constants, list of regs:", config_obj.get_constants_list_of_regs())

  print ("rng:", config_obj.get_label_addr_rng())
  