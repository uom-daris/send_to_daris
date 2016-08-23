# send_to_daris
A plugin app for [MyTardis](https://github.com/mytardis/mytardis) to send data to [DaRIS](https://github.com/uom-daris/daris).

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
  - 1) Edit **tardis/tardis_portal/views/pages.py**
    - a) Make a backup for file **tardis/tardis_portal/views/pages.py**
    - b) At the start of the file, import the plugin app moudles:
         ```python
         from tardis.apps.send_to_daris.views import (send_experiment, send_dataset)
         from tardis.apps.send_to_daris.config import SendToDaRISConfig
         ```

    - c) Find the following code block:
         ```python
         # Enables UI elements for the push_to app
         if c['push_to_enabled']:
             push_to_args = {
                 'dataset_id': dataset.pk
             }
             c['push_to_url'] = reverse(initiate_push_dataset,
                                        kwargs=push_to_args)
         ```
         
         insert the follwing lines right after the code block above:
         ```python
         # Enable UI elements for send_to_daris plugin app
         c['send_to_daris_enabled'] = SendToDaRISConfig.name in settings.INSTALLED_APPS
         if c['send_to_daris_enabled']:
            c['send_to_daris_url'] = reverse(send_dataset, kwargs={'dataset_id': dataset.pk})
         ```
 
    - d) Find the following code block:
         ```python
         # Enables UI elements for the push_to app
         c['push_to_enabled'] = PushToConfig.name in settings.INSTALLED_APPS
         if c['push_to_enabled']:
             push_to_args = {
                 'experiment_id': experiment.pk
             }
             c['push_to_url'] = reverse(initiate_push_experiment,
                                       kwargs=push_to_args)
         ```
         
         insert the following line right after the block above:
         ```python
         # Enables UI elements for send_to_daris plugin app
         c['send_to_daris_enabled'] = SendToDaRISConfig.name in settings.INSTALLED_APPS
         if c['send_to_daris_enabled']:
             c['send_to_daris_url'] = reverse(send_experiment, kwargs={'experiment_id': experiment.pk})
         ```

  - 2) Edit **tardis/tardis_portal/templates/tardis_portal/view_experiment.html**
    - a) Back up **tardis/tardis_portal/templates/tardis_portal/view_experiment.html**
    - b) Find the following block:
         ```
         {% if push_to_enabled and is_authenticated %}
         <a class="btn btn-mini btn-primary" title="Push to..."
            onclick="window.open('{{ push_to_url }}', 'push-to', 'width=800, height=600'); return false;"
            href="{{ push_to_url }}" target="_blank">
           <i class="icon-upload"></i>
           Push to...
         </a>
         {% endif %}
         ```
         
         Insert the following right after the above block:
         ```
         {% if send_to_daris_enabled and is_authenticated %}
         <a class="btn btn-mini btn-primary" title="Send to DaRIS..."
            onclick="window.open('{{ send_to_daris_url }}', 'Send to DaRIS', 'width=800, height=480'); return false;"
            href="{{ send_to_daris_url }}" target="_blank">
           <i class="icon-upload"></i>
           Send to DaRIS...
         </a>
         {% endif %}
         ```
 
  - 3) Edit **tardis/tardis_portal/templates/tardis_portal/view_dataset.html**
    - a) Back up **tardis/tardis_portal/templates/tardis_portal/view_dataset.html**
    - b) Find the following code block:
         ```
         {% if push_to_enabled and is_authenticated %}
         <a class="btn btn-mini btn-primary" title="Push to..."
            onclick="window.open('{{ push_to_url }}', 'push-to', 'width=800, height=600'); return false;"
            href="{{ push_to_url }}" target="_blank">
           <i class="icon-upload"></i>
           Push to...
         </a>
         {% endif %}
         ```

         Insert following code right after the above block:
         ```
         {% if send_to_daris_enabled and is_authenticated %}
         <a class="btn btn-mini btn-primary" title="Send to DaRIS..."
            onclick="window.open('{{ send_to_daris_url }}', 'Send to DaRIS', 'width=800, height=480'); return false;"
            href="{{ send_to_daris_url }}" target="_blank">
           <i class="icon-upload"></i>
           Send to DaRIS...
         </a>
         {% endif %}
         ```
6. Restart MyTardis web server and celeryd. Login to MyTardis, in Experiment view or Dataset view, you should see **'Send to DaRIS...** button.

## Configuration
  * See [how to configure the remote DaRIS server and projects to send data to via MyTardis Admin Interface.](http://nsp.nectar.org.au/resplat-wiki/doku.php?id=data_management:daris:interop:mytardis_plugin_app_send_to_daris#configuration)

## User's Guide
  * See [user's guide](http://nsp.nectar.org.au/resplat-wiki/doku.php?id=data_management:daris:interop:mytardis_plugin_app_send_to_daris#user_s_guide)
  * We also have a [youtube video](https://youtu.be/3ioBixZ6qmk) to demonstrate the process.

    [![Video Guide](https://img.youtube.com/vi/3ioBixZ6qmk/0.jpg)](https://www.youtube.com/watch?v=3ioBixZ6qmk)
