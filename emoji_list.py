import emoji
emoji_convertedImage = emoji.emojize()
emojiList = [
"+1",
"-1",
"100",
"1234",
"8ball",
"ab",
"abc",
"abcd",
"accept",
"adult",
"aerial_tramway",
"airplane_arriving",
"airplane_departure",
"alarm_clock",
"alien",
"ambulance",
"amphora",
"anchor",
"angel",
"anger",
"angry",
"anguished",
"ant",
"apple",
"aquarius",
"aries",
"arrow_double_down",
"arrow_double_up",
"arrow_down_small",
"arrow_up_small",
"arrows_clockwise",
"arrows_counterclockwise",
"art",
"articulated_lorry",
"astonished",
"athletic_shoe",
"atm",
"avocado",
"baby",
"baby_bottle",
"baby_chick",
"baby_symbol",
"back",
"bacon",
"badminton_racquet_and_shuttlecock",
"baggage_claim",
"baguette_bread",
"balloon",
"bamboo",
"banana",
"bank",
"bar_chart",
"barber",
"baseball",
"basketball",
"bat",
"bath",
"bathtub",
"battery",
"bear",
"bearded_person",
"bee",
"beer",
"beers",
"beetle",
"beginner",
"bell",
"bento",
"bicyclist",
"bike",
"bikini",
"billed_cap",
"bird",
"birthday",
"black_circle",
"black_heart",
"black_joker",
"black_large_square",
"black_medium_small_square",
"black_square_button",
"blossom",
"blowfish",
"blue_book",
"blue_car",
"blue_heart",
"blush",
"boar",
"boat",
"bomb",
"book",
"bookmark",
"bookmark_tabs",
"books",
"boom",
"boot",
"bouquet",
"bow",
"bow_and_arrow",
"bowl_with_spoon",
"bowling",
"boxing_glove",
"boy",
"brain",
"bread",
"breast-feeding",
"bride_with_veil",
"bridge_at_night",
"briefcase",
"broccoli",
"broken_heart",
"bug",
"bulb",
"bullettrain_front",
"bullettrain_side",
"burrito",
"bus",
"busstop",
"bust_in_silhouette",
"busts_in_silhouette",
"butterfly",
"cactus",
"cake",
"calendar",
"call_me_hand",
"calling",
"camel",
"camera",
"camera_with_flash",
"cancer",
"candy",
"canned_food",
"canoe",
"capital_abcd",
"capricorn",
"car",
"card_index",
"carousel_horse",
"carrot",
"cat",
"cat2",
"cd",
"champagne",
"chart",
"chart_with_downwards_trend",
"chart_with_upwards_trend",
"checkered_flag",
"cheese_wedge",
"cherries",
"cherry_blossom",
"chestnut",
"chicken",
"child",
"children_crossing",
"chocolate_bar",
"chopsticks",
"christmas_tree",
"church",
"cinema",
"circus_tent",
"city_sunrise",
"city_sunset",
"cl",
"clap",
"clapper",
"clinking_glasses",
"clipboard",
"clock1",
"clock10",
"clock1030",
"clock11",
"clock1130",
"clock12",
"clock1230",
"clock130",
"clock2",
"clock230",
"clock3",
"clock330",
"clock4",
"clock430",
"clock5",
"clock530",
"clock6",
"clock630",
"clock7",
"clock730",
"clock8",
"clock830",
"clock9",
"clock930",
"closed_book",
"closed_lock_with_key",
"closed_umbrella",
"clown_face",
"coat",
"cocktail",
"coconut",
"coffee",
"cold_sweat",
"collision",
"computer",
"confetti_ball"
"pill",
"pineapple",
"pisces",
"pizza",
"place_of_worship",
"point_down",
"point_left",
"point_right",
"point_up_2",
"police_car",
"poodle",
"poop",
"popcorn",
"post_office",
"postal_horn",
"postbox",
"potable_water",
"potato",
"pouch",
"poultry_leg",
"pound",
"pouting_cat",
"pray",
"prayer_beads",
"pregnant_woman",
"pretzel",
"prince",
"princess",
"punch",
"purple_heart",
"purse",
"pushpin",
"put_litter_in_its_place",
"question",
"rabbit",
"rabbit2",
"racehorse",
"radio",
"radio_button",
"rage",
"railway_car",
"rainbow",
"raised_back_of_hand",
"raised_hand",
"raised_hands",
"raising_hand",
"ram",
"ramen",
"rat",
"red_car",
"red_circle",
"relieved",
"repeat",
"repeat_one",
"restroom",
"reversed_hand_with_middle_finger_extended",
"revolving_hearts",
"rewind",
"rhinoceros",
"ribbon",
"rice",
"rice_ball",
"rice_cracker",
"rice_scene",
"right-facing_fist",
"ring",
"robot_face",
"rocket",
"roller_coaster",
"rolling_on_the_floor_laughing",
"rooster",
"rose",
"rotating_light",
"round_pushpin",
"rowboat",
"rugby_football",
"runner",
"running",
"running_shirt_with_sash",
"sagittarius",
"sailboat",
"sake",
"sandal",
"sandwich",
"santa",
"satellite_antenna",
"satisfied",
"sauropod",
"saxophone",
"scarf",
"school",
"school_satchel",
"scooter",
"scorpion",
"scorpius",
"scream",
"scream_cat",
"scroll",
"seat",
"second_place_medal",
"see_no_evil",
"seedling",
"selfie",
"serious_face_with_symbols_covering_mouth",
"shallow_pan_of_food",
"shark",
"shaved_ice",
"sheep",
"shell",
"ship",
"shirt",
"shit",
"shocked_face_with_exploding_head",
"shoe",
"shopping_trolley",
"shower",
"shrimp",
"shrug",
"shushing_face",
"sign_of_the_horns",
"signal_strength",
"six_pointed_star",
"ski",
"skin-tone-2",
"skin-tone-3",
"skin-tone-4",
"skin-tone-5",
"skin-tone-6",
"skull",
"sled",
"sleeping",
"sleeping_accommodation",
"sleepy",
"slightly_frowning_face",
"slightly_smiling_face",
"slot_machine",
"small_blue_diamond",
"small_orange_diamond",
"small_red_triangle",
"small_red_triangle_down",
"smile",
"smile_cat",
"smiley",
"smiley_cat",
"smiling_face_with_smiling_eyes_and_hand_covering_mouth",
"smiling_imp",
"smirk",
"smirk_cat",
"smoking",
"snail",
"snake",
"sneezing_face",
"snowboarder",
"snowman_without_snow",
"sob",
"soccer",
"socks",
"soon",
"sos",
"sound",
"space_invader",
"spaghetti",
"sparkler",
"sparkles",
"sparkling_heart",
"speak_no_evil",
"speaker",
"speech_balloon",
"speedboat",
"spock-hand",
"spoon",
"sports_medal",
"squid",
"star",
"star-struck",
"star2",
"stars",
"station",
"statue_of_liberty",
"steam_locomotive",
"stew",
"straight_ruler",
"strawberry",
"stuck_out_tongue",
"stuck_out_tongue_closed_eyes",
"stuck_out_tongue_winking_eye",
"stuffed_flatbread",
"sun_with_face",
"sunflower",
"sunglasses",
"sunrise",
"sunrise_over_mountains",
"surfer",
"sushi", 
"suspension_railway", 
"sweat", 
"sweat_drops", 
"sweat_smile", 
"sweet_potato", 
"swimmer", 
"symbols", 
"synagogue", 
"syringe", 
"t-rex", 
"table_tennis_paddle_and_ball", 
"taco", 
"tada", 
"takeout_box", 
"tanabata_tree", 
"tangerine", 
"taurus", 
"taxi", 
"tea", 
"telephone_receiver", 
"telescope", 
"tennis", 
"tent", 
"the_horns", 
"thinking_face", 
"third_place_medal", 
"thought_balloon", 
"thumbsdown", 
"thumbsup", 
"ticket", 
"tiger", 
"tiger2", 
"tired_face", 
"toilet", 
"tokyo_tower", 
"tomato", 
"tongue", 
"top", 
"tophat", 
"tractor", 
"traffic_light", 
"train", 
"train2", 
"tram", 
"triangular_flag_on_post", 
"triangular_ruler", 
"trident", 
"triumph", 
"trolleybus", 
"trophy", 
"tropical_drink", 
"tropical_fish", 
"truck", 
"trumpet", 
"tshirt", 
"tulip", 
"tumbler_glass", 
"turkey", 
"turtle", 
"tv", 
"twisted_rightwards_arrows", 
"two_hearts", 
"two_men_holding_hands", 
"two_women_holding_hands", 
"u5272", 
"u5408", 
"u55b6", 
"u6307", 
"u6709", 
"u6e80", 
"u7121", 
"u7533", 
"u7981", 
"u7a7a", 
"umbrella_with_rain_drops", 
"unamused", 
"underage", 
"unicorn_face", 
"unlock", 
"up", 
"upside_down_face", 
"vampire", 
"vertical_traffic_light", 
"vhs", 
"vibration_mode", 
"video_camera", 
"video_game", 
"violin", 
"virgo", 
"volcano", 
"volleyball", 
"vs", 
"walking", 
"waning_crescent_moon", 
"waning_gibbous_moon", 
"watch", 
"water_buffalo", 
"water_polo", 
"watermelon", 
"wave", 
"waving_black_flag", 
"waxing_crescent_moon", 
"waxing_gibbous_moon", 
"wc", 
"weary", 
"wedding", 
"whale", 
"whale2", 
"wheelchair", 
"white_check_mark", 
"white_circle", 
"white_flower", 
"white_large_square", 
"white_medium_small_square", 
"white_square_button", 
"wilted_flower", 
"wind_chime", 
"wine_glass", 
"wink", 
"wolf", 
"woman", 
"womans_clothes", 
"womans_hat", 
"womens", 
"worried", 
"wrench", 
"wrestlers", 
"x", 
"yellow_heart", 
"yen", 
"yum", 
"zany_face", 
"zap", 
"zebra_face", 
"zipper_mouth_face", 
"zombie", 
"zzz"
]

