"""
Inkycal Calendar Module
Copyright by aceinnolab
"""

# pylint: disable=logging-fstring-interpolation

import calendar as cal

from inkycal.custom import *
from inkycal.modules.template import inkycal_module

logger = logging.getLogger(__name__)


class Calendar(inkycal_module):
    """Calendar class
    Create monthly calendar and show events from given iCalendars
    """

    name = "Calendar - Show monthly calendar with events from iCalendars"

    optional = {
        "week_starts_on": {
            "label": "When does your week start? (default=Monday)",
            "options": ["Monday", "Sunday"],
            "default": "Monday",
        },
        "show_events": {
            "label": "Show parsed events? (default = True)",
            "options": [True, False],
            "default": True,
        },
        "ical_urls": {
            "label": "iCalendar URL/s, separate multiple ones with a comma",
        },
        "ical_files": {
            "label": "iCalendar filepaths, separated with a comma",
        },
        "ical_names": {
            "label": "iCalendar names seperated by a comma, e.g. John, Jane",
        },
        "date_format": {
            "label": "Use an arrow-supported token for custom date formatting "
                     + "see https://arrow.readthedocs.io/en/stable/#supported-tokens, e.g. D MMM",
            "default": "D MMM",
        },
        "time_format": {
            "label": "Use an arrow-supported token for custom time formatting "
                     + "see https://arrow.readthedocs.io/en/stable/#supported-tokens, e.g. HH:mm",
            "default": "HH:mm",
        },
    }

    def __init__(self, config):
        """Initialize inkycal_calendar module"""

        super().__init__(config)
        config = config['config']

        self.ical = None
        self.month_events = None
        self._upcoming_events = None
        self._days_with_events = None

        # optional parameters
        self.week_start = config['week_starts_on']
        self.show_events = config['show_events']
        self.date_format = config["date_format"]
        self.time_format = config['time_format']
        self.language = config['language']

        if config['ical_urls'] and isinstance(config['ical_urls'], str):
            self.ical_urls = config['ical_urls'].split(',')
        else:
            self.ical_urls = config['ical_urls']

        if config['ical_files'] and isinstance(config['ical_files'], str):
            self.ical_files = config['ical_files'].split(',')
        else:
            self.ical_files = config['ical_files']

        if config['ical_names'] and isinstance(config['ical_names'], str):
            self.ical_names = config['ical_names'].split(',')
        else:
            self.ical_names = config['ical_names']

        # additional configuration
        self.timezone = get_system_tz()
        self.num_font = ImageFont.truetype(
            fonts['NotoSans-SemiCondensed'], size=self.fontsize
        )

        # give an OK message
        logger.debug(f'{__name__} loaded')

    @staticmethod
    def flatten(values):
        """Flatten the values."""
        return [x for y in values for x in y]

    def generate_image(self):
        """Generate image for this module"""

        # Define new image size with respect to padding
        im_width = int(self.width - (2 * self.padding_left))
        im_height = int(self.height - (2 * self.padding_top))
        im_size = im_width, im_height
        events_height = 0

        logger.debug(f'Image size: {im_size}')

        # Create an image for black pixels and one for coloured pixels
        im_black = Image.new('RGB', size=im_size, color='white')
        im_colour = Image.new('RGB', size=im_size, color='white')

        # Allocate space for month-names, weekdays etc.
        month_name_height = int(im_height * 0.10)
        text_bbox_height = self.font.getbbox("hg")
        weekdays_height = int((abs(text_bbox_height[3]) + abs(text_bbox_height[1])) * 1.25)
        logger.debug(f"month_name_height: {month_name_height}")
        logger.debug(f"weekdays_height: {weekdays_height}")

        if self.show_events:
            logger.debug("Allocating space for events")
            calendar_height = int(im_height * 0.6)
            events_height = (
                    im_height - month_name_height - weekdays_height - calendar_height
            )
            logger.debug(f'calendar-section size: {im_width} x {calendar_height} px')
            logger.debug(f'events-section size: {im_width} x {events_height} px')
        else:
            logger.debug("Not allocating space for events")
            calendar_height = im_height - month_name_height - weekdays_height
            logger.debug(f'calendar-section size: {im_width} x {calendar_height} px')

        # Create a 7x6 grid and calculate icon sizes
        calendar_rows, calendar_cols = 6, 7
        icon_width = im_width // calendar_cols
        icon_height = calendar_height // calendar_rows
        logger.debug(f"icon_size: {icon_width}x{icon_height}px")

        # Calculate spacings for calendar area
        x_spacing_calendar = int((im_width % calendar_cols) / 2)
        y_spacing_calendar = int((im_height % calendar_rows) / 2)

        logger.debug(f"x_spacing_calendar: {x_spacing_calendar}")
        logger.debug(f"y_spacing_calendar :{y_spacing_calendar}")

        # Calculate positions for days of month
        grid_start_y = month_name_height + weekdays_height + y_spacing_calendar
        grid_start_x = x_spacing_calendar

        grid_coordinates = [
            (grid_start_x + icon_width * x, grid_start_y + icon_height * y)
            for y in range(calendar_rows)
            for x in range(calendar_cols)
        ]

        weekday_pos = [
            (grid_start_x + icon_width * _, month_name_height)
            for _ in range(calendar_cols)
        ]

        now = arrow.now(tz=self.timezone)

        # Set week-start of calendar to specified week-start
        if self.week_start == "Monday":
            cal.setfirstweekday(cal.MONDAY)
            week_start = now.shift(days=-now.weekday())
        else:
            cal.setfirstweekday(cal.SUNDAY)
            week_start = now.shift(days=-now.isoweekday())

        # Write the name of current month
        write(
            im_black,
            (0, 0),
            (im_width, month_name_height),
            str(now.format('MMMM', locale=self.language)),
            font=self.font,
            autofit=True,
        )

        # Set up week-names in local language and add to main section
        weekday_names = [
            week_start.shift(days=+_).format('ddd', locale=self.language)
            for _ in range(7)
        ]
        logger.debug(f'weekday names: {weekday_names}')

        for index, weekday in enumerate(weekday_pos):
            write(
                im_black,
                weekday,
                (icon_width, weekdays_height),
                weekday_names[index],
                font=self.font,
                autofit=True,
                fill_height=0.9,
            )

        # Create a calendar template and flatten (remove nesting)
        calendar_flat = self.flatten(cal.monthcalendar(now.year, now.month))
        # logger.debug(f" calendar_flat: {calendar_flat}")

        # Map days of month to co-ordinates of grid -> 3: (row2_x,col3_y)
        grid = {}
        for i in calendar_flat:
            if i != 0:
                grid[i] = grid_coordinates[calendar_flat.index(i)]
        # logger.debug(f"grid:{grid}")

        # remove zeros from calendar since they are not required
        calendar_flat = [num for num in calendar_flat if num != 0]

        # ensure all numbers have the same size
        fontsize_numbers = int(min(icon_width, icon_height) * 0.5)
        number_font = ImageFont.truetype(self.font.path, fontsize_numbers)

        # Add the numbers on the correct positions
        for number in calendar_flat:
            if number != int(now.day):
                write(
                    im_black,
                    grid[number],
                    (icon_width, icon_height),
                    str(number),
                    font=number_font,
                )

        # Draw a red/black circle with the current day of month in white
        icon = Image.new('RGBA', (icon_width, icon_height))
        current_day_pos = grid[int(now.day)]
        x_circle, y_circle = int(icon_width / 2), int(icon_height / 2)
        radius = int(icon_width * 0.2)
        ImageDraw.Draw(icon).ellipse(
            (
                x_circle - radius,
                y_circle - radius,
                x_circle + radius,
                y_circle + radius,
            ),
            fill='black',
            outline=None,
        )
        write(
            icon,
            (0, 0),
            (icon_width, icon_height),
            str(now.day),
            font=self.num_font,
            fill_height=0.5,
            colour='white',
        )
        im_colour.paste(icon, current_day_pos, icon)

        # If events should be loaded and shown...
        if self.show_events:

            # If this month requires 5 instead of 6 rows, increase event section height
            if len(cal.monthcalendar(now.year, now.month)) == 5:
                events_height += icon_height

            # If this month requires 4 instead of 6 rows, increase event section height
            elif len(cal.monthcalendar(now.year, now.month)) == 4:
                events_height += icon_height * 2

            # import the ical-parser
            # pylint: disable=import-outside-toplevel
            from inkycal.modules.ical_parser import iCalendar

            # find out how many lines can fit at max in the event section
            line_spacing = 2
            text_bbox_height = self.font.getbbox("hg")
            line_height = text_bbox_height[3] - text_bbox_height[1] + line_spacing
            max_event_lines = events_height // (line_height + line_spacing)

            # generate list of coordinates for each line
            events_offset = im_height - events_height
            event_lines = [
                (0, events_offset + int(events_height / max_event_lines * _))
                for _ in range(max_event_lines)
            ]

            # logger.debug(f"event_lines {event_lines}")

            # timeline for filtering events within this month
            month_start = arrow.get(now.floor('month'))
            month_end = arrow.get(now.ceil('month'))

            # fetch events from given iCalendars
            self.ical = iCalendar()
            parser = self.ical

            

            if self.ical_urls:
                parser.load_url(self.ical_urls)
                # I should put a for each here.
            if self.ical_files:
                parser.load_from_file(self.ical_files)



            print(len(parser.icalendars))

            # Filter events for full month (even past ones) for drawing event icons
            month_events = parser.get_events(month_start, month_end, self.timezone)
            #print(month_events)
            parser.sort()
            self.month_events = month_events

            # Initialize days_with_events as an empty list
            days_with_events = {}

            for event in month_events:
                start = arrow.get(event['begin'].date(), tzinfo=self.timezone)
                end = arrow.get(event['end'].date(), tzinfo=self.timezone)

                calendar_index = event['calendar_index']  # Use the stored integer directly

                for day in arrow.Arrow.range('day', start, end):
                    day_num = int(day.format('D'))
                    if day_num not in days_with_events:
                        days_with_events[day_num] = set()

                    days_with_events[day_num].add(calendar_index)

            self._days_with_events = sorted(days_with_events.keys())

            for day_num, calendar_indices in days_with_events.items():
                print("Current day number")
                print(day_num)
                print("Current calendar index")
                print(calendar_indices)
                if day_num in grid:

                    if {0, 1}.issubset(calendar_indices):  # Checks if both 0 and 1 are present
                        print(f"Day {day_num} contains both calendar indices 0 and 1")

                        # Draw dashed alternating black and color
                        #draw_border(im_colour, grid[day_num], (icon_width, icon_height), radius=6, thickness = 4, dashed=True)
                        #draw_border(im_black, grid[day_num], (icon_width, icon_height), radius=6, thickness = 4, dashed=True, invert=True)

                        #Draw nested
                        draw_border(im_black, grid[day_num], (icon_width, icon_height), radius=6, thickness = 3)

                        offset = 7
                        #Draw both a black border AND a red border
                        xy = grid[day_num]
                        xy = (xy[0] + offset, xy[1] + offset)  # Create a new tuple
                        draw_border(im_colour, xy, (icon_width-2*offset, icon_height-2*offset), radius=6, thickness = 3)

                    else:
                        if 0 in calendar_indices:
                            draw_border(im_black, grid[day_num], (icon_width, icon_height), radius=6, thickness = 3)
                        if 1 in calendar_indices:
                            draw_border(im_colour, grid[day_num], (icon_width, icon_height), radius=6, thickness = 3)


            # Filter upcoming events until 4 weeks in the future
            parser.clear_events()
            upcoming_events = parser.get_events(now, now.shift(weeks=4), self.timezone)
            self._upcoming_events = upcoming_events

            # delete events which won't be able to fit (more events than lines)
            upcoming_events = upcoming_events[:max_event_lines]

            # Check if any events were found in the given timerange
            if upcoming_events:

                # Find out how much space (width) the date format requires
                lang = self.language

                date_width = int(max((
                    self.font.getlength(events['begin'].format(self.date_format, locale=lang))
                    for events in upcoming_events)) * 1.1
                                 )

                time_width = int(max((
                    self.font.getlength(events['begin'].format(self.time_format, locale=lang))
                    for events in upcoming_events)) * 1.1
                                 )

                text_bbox_height = self.font.getbbox("hg")
                line_height = text_bbox_height[3] + line_spacing



                event_width_s = im_width - date_width - time_width
                event_width_l = im_width - date_width

                # Display upcoming events below calendar TODO: not used?
                # tomorrow = now.shift(days=1).floor('day')
                # in_two_days = now.shift(days=2).floor('day')

                #Bad hardcoded practice. This wont work if we have more than 2 calendars...
                #The data should be in a matrix or table or something.
                # Create a dictionary to hold events grouped by their calendar_index
                events_by_index = {}

                # Loop through each event and group by calendar_index
                for event in upcoming_events:
                    index = event['calendar_index']
                    if index not in events_by_index:
                        events_by_index[index] = []  # Initialize a list for this index if not already present
                    events_by_index[index].append(event)

                # Now you can access all events for a specific calendar_index like this:
                for index in sorted(events_by_index.keys()):
                    #print(f"Events for Calendar Index {index}:")
                    cursor = 0
                    shift_right = index == 1
                    #Hardcoded, not pretty...
                    shift_offset = im_width // 2 if shift_right else 0  # Move to the middle for index 1


                    #
                    #if self.ical_names:
                    #    print(self.ical_names[0])

                    #    print(self.ical_names[1])

                    if(shift_right):

                        draw_border(
                            im_colour, 
                            (shift_offset, event_lines[cursor+1][1]),
                            (date_width, line_height*1.5),
                            radius=6, 
                            thickness = 4
                        )

                        if self.ical_names[1]:
                            write(
                                im_black,
                                (date_width + shift_offset, event_lines[cursor][1]),
                                (event_width_l, line_height*3),
                                " "+self.ical_names[1], #Event_width_l should match the length of the string
                                font=self.font,
                                alignment='left',
                                autofit=True
                            )

                    else:
                        draw_border(
                            im_black, 
                            (shift_offset, event_lines[cursor+1][1]),
                            (date_width, line_height*1.5),
                            radius=6,
                            thickness = 4
                        )
                        if self.ical_names[0]:

                            write(
                                im_black,
                                (date_width + shift_offset, event_lines[cursor][1]),
                                (event_width_l, line_height*3),
                                " " + self.ical_names[0],
                                font=self.font,
                                alignment='left',
                                autofit=True
                            )
                    cursor +=3

                    for event in events_by_index[index]:

                        if cursor < len(event_lines):
                            event_duration = (event['end'] - event['begin']).days
                            if event_duration > 1:
                                # Format the duration using Arrow's localization
                                days_translation = arrow.get().shift(days=event_duration).humanize(only_distance=True,
                                                                                                locale=lang)
                                the_name = f"{event['title']} ({days_translation})"
                            else:
                                the_name = event['title']
                            the_date = event['begin'].format(self.date_format, locale=lang)
                            the_time = event['begin'].format(self.time_format, locale=lang)
                            # logger.debug(f"name:{the_name}   date:{the_date} time:{the_time}")





                            if now < event['end']:
                                write(
                                    im_colour,
                                    (shift_offset, event_lines[cursor][1]),
                                    (date_width, line_height),
                                    the_date,
                                    font=self.font,
                                    alignment='left',
                                )

                                # Check if event is all day
                                if parser.all_day(event):
                                    write(
                                        im_black,
                                        (date_width + shift_offset, event_lines[cursor][1]),
                                        (event_width_l, line_height),
                                        the_name,
                                        font=self.font,
                                        alignment='left',
                                    )
                                else:
                                    write(
                                        im_black,
                                        (date_width+ shift_offset, event_lines[cursor][1]),
                                        (time_width, line_height),
                                        the_time,
                                        font=self.font,
                                        alignment='left',
                                    )

                                    write(
                                        im_black,
                                        (date_width + time_width + shift_offset, event_lines[cursor][1]),
                                        (event_width_s, line_height),
                                        the_name,
                                        font=self.font,
                                        alignment='left',
                                    )

                                
                                cursor += 1
            else:
                symbol = '- '

                while self.font.getlength(symbol) < im_width * 0.9:
                    symbol += ' -'
                write(
                    im_black,
                    event_lines[0],
                    (im_width, line_height),
                    symbol,
                    font=self.font,
                )

        # return the images ready for the display
        return im_black, im_colour
