chitte à dou

a play on "shit to do"

problem, interfaces for event sites suck - too many of them, too much garbage "chitte"

after using some of the latest chat tools - realized that they are way better for aggregating and understanding events and helping with planning.

kind of a no click set of planning if you are on audio.

but reading a list is better for other situations.

but the list are kind of eh - newspapers have unstructured long lists, event sites want to sell you DIY escape rooms run out of public restrooms.
 the site barpeople has a nice simple aggregation function, but the wrapper site - i'd like to do some thing different with. https://www.barpeople.com/albany-county-weekly-live-music

but basically a simple list.

so at a high level the thought for the technical architecture is:


script - prob python - run in github actions
this script takes two configuration files and a set of runtime properties
    runtime properties:
        Grok API Key


    configuration 1: the recurrant logic
        this recurrant logic runs and gets all the events and places the file in the target location
        the configuration file consists of at least the following
            a set of model configuration and runtime paramaters
            a set of prompts about source locations
            a set of prompts about regional focus
            a set of predilictions of the user (user defined)
            a set of guidelines regarding branding of the platform
            a json format for structured out output

            this outputs a json file in the same locaiton which is available as a data source to github pages

    configuration 2: the interface
        this set of code will represent the static portion which will render the output generated from configuration 1 as a sourced file, and the user interface will present a lightweight list of events

        





