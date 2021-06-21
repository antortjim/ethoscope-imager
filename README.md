## Ethoscope imager

# A module to easily interface with ethoscope sqlite files (dbfiles). It provides an OOP implementation of the script in https://github.com/gilestrolab/ethoscope/blob/master/scripts/tools/db2video.py


# How to use

## Just getting frames to a newly created IMG_SNAPSHOTS folder next to the sqlite file

Get the first 10 snapshots

```
./imager.py  --path /ethoscope_data/results/008aad42625f433eb4bd2b44f811738e/ETHOSCOPE_008/2021-06-18_16-52-43/2021-06-18_16-52-43_008aad42625f433eb4bd2b44f811738e.db --id 1 2 3 4 5 6 7 8 9 10
```

Get the snapshot happening at t = 10000 ms (10s)
```
./imager.py  --path /ethoscope_data/results/008aad42625f433eb4bd2b44f811738e/ETHOSCOPE_008/2021-06-18_16-52-43/2021-06-18_16-52-43_008aad42625f433eb4bd2b44f811738e.db --t 10000
```

## Annotate all frames under the IMG_SNAPSHOTS folder
```
./imager.py  --path /ethoscope_data/results/008aad42625f433eb4bd2b44f811738e/ETHOSCOPE_008/2021-06-18_16-52-43/2021-06-18_16-52-43_008aad42625f433eb4bd2b44f811738e.db --annotate
```

## Make a video called video.mp4 using all snapshots
```
./imager.py  --path /ethoscope_data/results/008aad42625f433eb4bd2b44f811738e/ETHOSCOPE_008/2021-06-18_16-52-43/2021-06-18_16-52-43_008aad42625f433eb4bd2b44f811738e.db --video
```









