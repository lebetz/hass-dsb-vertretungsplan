[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)


## Support Heinrich-Hertz-Schule, Hamburg, Vertretungsplan in Home Assistant

### Note:

* This integration only makes sense to you, if your kid is attending the Heinrich-Hertz-Schule in Hamburg, Germany.
* You will need a user name and a password to access the data. Please ask your Elternvertreter.
    
  
## Setup

### Installation:
* Go to HACS -> Integrations
* Click the three dots on the top right and select `Custom Repositories`
* Enter `https://github.com/lebetz/hass-dsb-vertretungsplan` as repository, select the category `Integration` and click Add
* A new custom integration shows up for installation (DSB Vertretungsplan) - install it
* Restart Home Assistant
  
  
### Configuration:
* Go to Configuration -> Integrations
* Click `Add Integration`
* Search for `DSB Vertretungsplan` and select it
* Specify the tutor group (Klasse) your kid is attending
* Add your user name and password
* If you have more than one kid, you can repeat the process and get one sensor per kid
  
  
## Usage:

The integration provides a `binary_sensor` for the tutor group your kid is attending. The sensor has a list of all current
classes that will be substituted or not take place according to the current planning of the school.
  
### Entities:

Provided you did the setup for tutor group ´7f´ you get the following sensor:

| Entity ID                      | Type               |  Description                                                               |
|--------------------------------|--------------------|----------------------------------------------------------------------------|
| binary_sensor.dsb_7f           | Binary Sensor      |  Is on, if there is Vertretung today, for 7f. See attributes for details   |

### Attributes:

The sensor has two attributes:

| Name               | Content                                                                                                 |
|--------------------|---------------------------------------------------------------------------------------------------------|
| status             | Date and time of when the data was updated by the school (not the sensor)                               |
| vertretung         | List of classes that are cancelled or substituted                                                       |

The list has the following attributes for each class that is cancelled or substituted:

| List attribute     | Content                                                                                                 |
|--------------------|---------------------------------------------------------------------------------------------------------|
| datum              | The date when the substitution takes place                                                              |
| klasse             | The tutor group affected. This will be the tutor group you configured the sensor for, or `alle`         |
| stunde             | Timing of the class affected                                                                            |
| vertreter          | The stand-in teacher taking care of the kids                                                            |
| fach               | The class affected                                                                                      |
| raum               | Which room is affected. This is where the kids where originally supposed to be                          |
| text               | Some informational text from the school, e.g. if kids stay in their own classroom                       |
| nach               | Some further information                                                                                |
| day                | The school day of the week - that's easier to read for the kids, but somewhat redundant to `datum`      |

### Display:

There is no dedicated Lovelace card for this, and showing lists is not very common in Home Assistant.
I suggest the following configuration to display the sensor:

```yaml
type: custom:stack-in-card
mode: vertical
cards:
  - type: entities
    entities:
      - type: custom:template-entity-row
        entity: binary_sensor.dsb_7f
        color: |-
          {% if is_state(config.entity, 'Vertretung') %}
            #FDD835
          {% endif %}
        secondary: >-
          Status von  {{ as_timestamp(state_attr(config.entity, 'last_update'))
          | timestamp_custom('%-H:%M Uhr am %A') }}
  - type: conditional
    conditions:
      - entity: binary_sensor.dsb_7f
        state: Vertretung
    card:
      type: custom:flex-table-card
      entities:
        include: binary_sensor.dsb_7f
      columns:
        - data: vertretung
          modify: x.day
          name: Tag
        - data: vertretung
          modify: x.lesson
          name: Stunde
        - data: vertretung
          modify: x.new_subject
          name: Fach
        - data: vertretung
          modify: x.new_room
          name: Raum
        - data: vertretung
          modify: x.subject
          name: (Fach)
        - data: vertretung
          modify: x.text
          name: Info

```

This results in the following card:

![Lovelace Card](images/lovelace.png)

Note, that this requires two custom frontend cards: `custom:stack-in-card`, `custom:template-entity-row` and `custom:flex-table-card`
which need to be installed via HACS as well. They are part of the HACS index and can be found with the built-in search.
