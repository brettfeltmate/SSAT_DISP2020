# -*- coding: utf-8 -*-

__author__ = "Brett Feltmate"

# TODO: Instructions need a bit of proofing.
# TODO: Settle on size of spatial array
# TODO: Once size is determined, set jitter values appropriately to prevent overlap
# TODO: Ensure condition rules are being followed
# TODO: Add commenting.
# TODO: Pilot to see if stim durations are appropriate now that there's masking.
# TODO: Ensure data is appropriately recorded & outputted.
# TODO: It would be nice to fix the post RSVP stream delay
# TODO: It would also be nice to find a better way to generate array coordinates


# KLibs packages employed
import klibs
from klibs import P
from klibs.KLUtilities import deg_to_px, TK_MS, TK_S, hide_mouse_cursor
from klibs.KLResponseCollectors import RC_KEYPRESS, KeyMap, KeyPressResponse
from klibs.KLGraphics import KLDraw as kld
from klibs.KLGraphics import fill, blit, flip, clear
from klibs.KLCommunication import message
from klibs.KLUserInterface import any_key, ui_request
from klibs.KLTime import CountDown, Stopwatch
from klibs.KLEventInterface import TrialEventTicket as ET
from klibs.KLResponseCollectors import *

# External libraries
import random
import sdl2

# Useful constants
PRESENT = 'present'
ABSENT = 'absent'

SPACE = "space"
TIME = "time"

HIGH = 'high'
LOW = 'low'

WHITE = (255, 255, 255, 255)

ITEM_DURATION = 0.150
MASK_DURATION = 0.050


class SSAT_DISP2020(klibs.Experiment):

    def setup(self):

        self.fix_size = deg_to_px(0.8)
        self.fix_thickness = deg_to_px(0.1)

        self.item_size = deg_to_px(0.8)

        self.fixation = kld.FixationCross(
            size=self.fix_size,
            thickness=self.fix_thickness,
            fill=WHITE
        )

        # Create array of possible stimulus locations for spatial search
        # When it comes time to present stimuli, a random jitter will be applied
        # to each item presented.

        self.spatial_array_locs = []
        offset = deg_to_px(4.0)
        for x in range(1, 3):
            for y in range(1, 3):
                loc1 = [P.screen_c[0] - offset * x, P.screen_c[1] - offset * y]
                loc2 = [P.screen_c[0] + offset * x, P.screen_c[1] + offset * y]
                loc3 = [P.screen_c[0] - offset * x, P.screen_c[1] + offset * y]
                loc4 = [P.screen_c[0] + offset * x, P.screen_c[1] - offset * y]

                self.spatial_array_locs.append(loc1)
                self.spatial_array_locs.append(loc2)
                self.spatial_array_locs.append(loc3)
                self.spatial_array_locs.append(loc4)

            loc5 = [P.screen_c[0] + offset * x, P.screen_c[1]]
            loc6 = [P.screen_c[0] - offset * x, P.screen_c[1]]
            loc7 = [P.screen_c[0], P.screen_c[1] + offset * x]
            loc8 = [P.screen_c[0], P.screen_c[1] - offset * x]
            self.spatial_array_locs.append(loc5)
            self.spatial_array_locs.append(loc6)
            self.spatial_array_locs.append(loc7)
            self.spatial_array_locs.append(loc8)


        coinflip = random.choice([True, False])

        if coinflip:
            self.present_key, self.absent_key = 'z', '/'
            self.keymap = KeyMap(
                "response", ['z', '/'],
                [PRESENT, ABSENT],
                [sdl2.SDLK_z, sdl2.SDLK_SLASH]
            )

        else:
            self.present_key, self.absent_key = '/', 'z'
            self.keymap = KeyMap(
                "response", ['/', 'z'],
                [PRESENT, ABSENT],
                [sdl2.SDLK_SLASH, sdl2.SDLK_z]
            )

        self.anykey_txt = "{0}\n\nPress any key to continue..."

        self.general_instructions = (
            "In this experiment you will see a series of items, amongst these items\n"
            "a target item may, or may not, be presented.\n If you see the target item "
            "press the '{0}' key, if the target item wasn't presented press the '{1}' instead.\n\n"
            "The experiment will begin with a few practice rounds to give you a sense of the task."
        ).format(self.present_key, self.absent_key)

        self.spatial_instructions = (
            "Searching in Space!\n\nIn these trials you will see a bunch of items scattered"
            "around the screen.\nIf one of them is the target, press the '{0}' key as fast as possible."
            "\nIf none of them are the target, press the '{1}' key as fast as possible."
        ).format(self.present_key, self.absent_key)

        self.temporal_instructions = (
            "Searching in Time!\n\nIn these trials you will see a series of items presented one\n"
            "at a time, centre-screen. If one of these items is the target, press the '{0}' key.\n"
            "If, by the end, none of them was the target, press the '{1}' key instead."
        ).format(self.present_key, self.absent_key)

        # Setup search conditions (blocked)
        self.spatial_conditions = [[HIGH, LOW], [HIGH, HIGH], [LOW, HIGH], [LOW, LOW]]
        random.shuffle(self.spatial_conditions)

        self.temporal_conditions = [[HIGH, LOW], [HIGH, HIGH], [LOW, HIGH], [LOW, LOW]]
        random.shuffle(self.temporal_conditions)

        self.practice_conditions = [[HIGH, LOW], [HIGH, HIGH], [LOW, HIGH], [LOW, LOW]]
        random.shuffle(self.practice_conditions)

        self.search_type = random.choice([SPACE, TIME])

        if P.run_practice_blocks:
            self.insert_practice_block(
                block_nums=[1, 2, 3, 4],
                trial_counts=P.trials_per_practice_block)

        general_msg = self.anykey_txt.format(self.general_instructions)
        self.blit_msg(general_msg, "left")
        any_key()

    def block(self):
        self.search_type = SPACE if self.search_type == TIME else TIME

        if not P.practicing:
            if self.search_type == SPACE:
                self.condition = self.spatial_conditions.pop()
            else:
                self.condition = self.temporal_conditions.pop()
        else:
            self.condition = self.practice_conditions.pop()

        self.target_distractor, self.distractor_distractor = self.condition

        self.create_stimuli(self.target_distractor, self.distractor_distractor)

        self.present_instructions()

    def setup_response_collector(self):
        self.rc.uses(RC_KEYPRESS)

        self.rc.keypress_listener.interrupts = True
        self.rc.keypress_listener.key_map = self.keymap

        timeout = 10 if self.search_type == SPACE else 100
        self.rc.terminate_after = [timeout, TK_S]

    def trial_prep(self):
        if self.search_type == SPACE:
            self.search_stimuli = self.prepare_spatial_array()
            self.rc.display_callback = self.present_spatial_array
            self.rc.display_kwargs = {'spatial_array': self.search_stimuli}

        else:
            self.search_stimuli = self.prepare_temporal_stream()
            self.rc.display_callback = self.present_temporal_stream
            self.rc.display_kwargs = {'temporal_stream': self.search_stimuli}

        events = [[1000, 'present_example_target']]
        events.append([events[-1][0] + 1000, 'present_fixation'])
        events.append([events[-1][0] + 1000, 'search_onset'])

        for e in events:
            self.evm.register_ticket(ET(e[1], e[0]))

        self.trial_sw = Stopwatch()
        self.present_target()
        hide_mouse_cursor()

    def trial(self):
        while self.evm.before("present_fixation", True):
            ui_request()

        self.blit_img(self.fixation, 5, P.screen_c)

        while self.evm.before("search_onset", True):
            ui_request()

        if self.search_type == SPACE:
            self.rc.collect()

        else:
            try:
                self.target_onset = 'NA'
                self.target_sw = Stopwatch()
                self.rc.collect()
            except IndexError:

                pass

        if len(self.rc.keypress_listener.responses):
            response, rt = self.rc.keypress_listener.response()
            if response != self.present_absent:
                self.present_feedback()

        else:
            response, rt = 'None', 'NA'

        clear()

        return {
            "practicing": str(P.practicing),
            "block_num": P.block_number,
            "trial_num": P.trial_number,
            "search_type": self.search_type,
            "stimulus_type": "LINE" if P.condition == 'line' else "COLOUR",
            "present_absent": self.present_absent,
            "set_size": self.set_size if self.search_type == SPACE else 'NA',
            "target_distractor": self.target_distractor,
            "distractor_distractor": self.distractor_distractor,
            "target_onset": self.target_onset if self.search_type == TIME else 'NA',
            "response": response,
            "rt": rt,
            "error": str(response != self.present_absent)
        }

    def trial_clean_up(self):
        self.rc.keypress_listener.reset()
        self.search_stimuli = []

    def clean_up(self):
        pass

    def present_target(self):
        msg = "This is your target!"
        msg_loc = [P.screen_c[0], P.screen_c[1] - deg_to_px(2.0)]

        fill()
        message(msg, location=msg_loc, registration=5)
        blit(self.target_item, location=P.screen_c, registration=5)
        flip()

    def prepare_spatial_array(self):
        spatial_array_locs = list(self.spatial_array_locs)
        random.shuffle(spatial_array_locs)

        self.item_locs = []

        for i in range(0, self.set_size):
            jitter = [x * 0.1 for x in range(-5, 5)]
            x_jitter = deg_to_px(random.choice(jitter))
            y_jitter = deg_to_px(random.choice(jitter))

            loc = spatial_array_locs.pop()
            loc[0], loc[1] = loc[0] + x_jitter, loc[1] + y_jitter

            self.item_locs.append(loc)



        spatial_array = []

        if self.present_absent == PRESENT:
            target_loc = self.item_locs.pop()
            spatial_array.append([self.target_item, target_loc])

        for loc in self.item_locs:
            distractor = random.choice(self.distractors)
            spatial_array.append([distractor, loc])

        return spatial_array

    def present_spatial_array(self, spatial_array):
        fill()
        blit(self.fixation, registration=5, location=P.screen_c)
        for item in spatial_array:
            blit(item[0], registration=5, location=item[1])
        flip()

    def prepare_temporal_stream(self):
        stream_length = 16

        temporal_stream = []

        if self.present_absent == PRESENT:
            self.target_time = random.randint(5, 12)
        else:
            self.target_time = -1

        for i in range(stream_length):
            if i == self.target_time:
                temporal_stream.append([self.target_item, True])

            else:
                distractor = random.choice(self.distractors)
                temporal_stream.append([distractor, False])

        return temporal_stream

    def present_temporal_stream(self, temporal_stream):
        duration_cd = CountDown(ITEM_DURATION, start=False)
        mask_cd = CountDown(MASK_DURATION, start=False)

        response_window = CountDown(2, start=False)

        last_item = True if len(temporal_stream) == 1 else False

        item = temporal_stream.pop()

        if item[1]:
            self.target_onset = self.target_sw.elapsed()

        duration_cd.start()
        while duration_cd.counting():
            self.blit_img(item[0], reg=5, loc=P.screen_c)

        mask_cd.start()
        while mask_cd.counting():
            self.blit_img(self.mask, reg=5, loc=P.screen_c)

        if last_item:
            clear()
            response_window.start()
            while response_window.counting():
                fill()
                flip()

    def present_instructions(self):
        block_txt = "Block {0} of {1}\n\n".format(P.block_number, P.blocks_per_experiment)

        if self.search_type == SPACE:
            block_txt += self.spatial_instructions
        else:
            block_txt += self.temporal_instructions

        if P.practicing:
            block_txt += "\n\n(This is a practice block)"

        block_txt = self.anykey_txt.format(block_txt)
        self.blit_msg(block_txt, "left")
        any_key()

    def present_feedback(self):
        msg = "Incorrect!"

        self.blit_msg(msg, 'left')

        feedback_cd = CountDown(0.5)
        while feedback_cd.counting():
            ui_request()

    def blit_msg(self, msg, align):
        msg = message(msg, align=align, blit_txt=False)

        fill()
        blit(msg, registration=5, location=P.screen_c)
        flip()

    def blit_img(self, img, reg, loc):
        fill()
        blit(img, registration=reg, location=loc)
        flip()

    def create_stimuli(self, tdSimilarity, ddSimilarity):
        # Setup target properties
        if P.condition == 'line':
            self.target_angle = random.randint(0, 179)
            self.target_height = deg_to_px(0.1)
            self.target_fill = WHITE

            self.target_item = kld.Rectangle(
                width=self.item_size,
                height=self.target_height,
                fill=WHITE,
                rotation=self.target_angle
            )

            if tdSimilarity == HIGH:
                self.ref_angle = self.target_angle
            else:
                self.ref_angle = self.target_angle + 90

            self.mask = kld.Asterisk(
                size=self.item_size,
                thickness=self.target_height,
                fill=WHITE,
                spokes=12
            )

        else:
            self.target_height = self.item_size
            self.palette = kld.ColorWheel(diameter=self.item_size)
            self.target_angle = random.randint(0, 359)
            self.target_colour = self.palette.color_from_angle(self.target_angle)

            self.target_item = kld.Rectangle(
                width=self.item_size,
                height=self.target_height,
                fill=self.target_colour
            )

            if tdSimilarity == HIGH:
                self.ref_angle = self.target_angle
            else:
                self.ref_angle = self.target_angle + 180

            self.mask = kld.Rectangle(
                width=self.item_size,
                fill=WHITE
            )

        # Setup distractor(s) properties
        if ddSimilarity == HIGH:
            padding = [random.choice([-20, 20])]
        else:
            padding = [-40, -20, 20, 40]

        self.distractors = []

        if P.condition == 'line':
            for p in padding:
                rotation = self.ref_angle + p

                self.distractors.append(
                    kld.Rectangle(
                        width=self.item_size,
                        height=self.target_height,
                        fill=WHITE,
                        rotation=rotation
                    )
                )
        else:
            for p in padding:
                colour = self.palette.color_from_angle(self.ref_angle + p)
                self.distractors.append(
                    kld.Rectangle(
                        width=self.item_size,
                        height=self.target_height,
                        fill=colour
                    )
                )
