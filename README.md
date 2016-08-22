# send_to_daris
A plugin app for MyTardis (Django) to send data to DaRIS

## Installation

1. Clone **send_to_daris** into your mytardis apps directory:
  * `cd /opt/mytardis/tardis/apps`
  * `git clone https://github.com/uom-daris/send_to_daris.git`
2. Add **send_to_daris** plugin app to the INSTALLED_APPS setting in **tardis/settings.py**:
  * `INSTALLED_APPS += ('tardis.apps.send_to_daris',)`
3. Initialise the app database:
  * `python mytardis.py migrate`
4. Initialise the static resources for the web portal
  * `python mytardis.py collectstatic`
5. Insert UI elements to MyTardis web portal
  - Edit **tardis/tardis_portal/views/pages.py**
    - a. At the top of the moudle:
         ```python
         from tardis.apps.send_to_daris.views import (send_experiment, send_dataset)
         from tardis.apps.send_to_daris.config import SendToDaRISConfig
         ```

    - b. Find the follow code block:
         ```python
         # Enables UI elements for the push_to app
         if c['push_to_enabled']:
             push_to_args = {
                 'dataset_id': dataset.pk
             }
             c['push_to_url'] = reverse(initiate_push_dataset,
                                        kwargs=push_to_args)
         ```
         
         add the follwing lines:
         ```python
         # send_to_daris
         c['send_to_daris_enabled'] = SendToDaRISConfig.name in settings.INSTALLED_APPS
         if c['send_to_daris_enabled']:
            c['send_to_daris_url'] = reverse(send_dataset, kwargs={'dataset_id': dataset.pk})
         ```

  - Edit tardis/tardis_portal/templates/view_experiment.html
  - Edit tardis/tardis_portal/templates/view_dataset.html
