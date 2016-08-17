from django.db import models

"""
  DarisServer and DarisProject models. The models are registered in admin.py.
"""


class DarisServer(models.Model):
    name = models.CharField('Nick name', max_length=32)
    host = models.CharField('Server host', max_length=128)
    port = models.PositiveIntegerField('Server port', default=443)
    transport = models.CharField('Server transport', max_length=6, default='https',
                                 choices=(('https', "HTTPS"), ('http', "HTTP")))

    def __unicode__(self):
        return self.name + ' | ' + self.transport + '://' + self.host + ':' + str(self.port)


class DarisProject(models.Model):
    server = models.ForeignKey('DarisServer', on_delete=models.CASCADE, )
    cid = models.CharField('Project ID', max_length=256)
    name = models.CharField('Project Name', max_length=256, blank=True)
    token = models.TextField('Access Token', max_length=256)

    def __unicode__(self):
        if self.name:
            return self.server.name + '/project/' + self.cid
        else:
            return self.server.name + '/project/' + self.cid + ' - ' + self.name
