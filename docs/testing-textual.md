# Testing textual notes 

As there is no documentation for unit testing a textual app. I thought i would write up some notes on how to do unit testing for my benefit (as i will probably forget this :slightly_smiling_face:) and others (might eventually take some of this and move into textual documentation, If this doesn't get documented)

## how does it work ?

The way it works is that the `App` class has a special method called `run_test()` which runs the app in a headless mode and returns a context that has methods to simulate
pressing keys, hovering mouse etc. While this isn't documented there are some really good [examples](https://github.com/Textualize/textual/tree/main/tests) in the textual repo test folder. 
See this [discussion](https://github.com/Textualize/textual/discussions/2506#discussioncomment-5827644) for more info


