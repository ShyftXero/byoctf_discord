# byoctf_discord
## Bring Your Own [Challenge || Capture] The Flag
Whoa... this is harder to do that I thought it would be... CTFs are fun.

I wanted to build this for the next iteration of SOTB or any CTF that fs2600 crew participates in running. 

This incarnation lives in the Arkansas Hackers discord server as a bot. 

It's meant to be interacted with primarily via DM, but there are a couple of reasons to interact with it in a public channel. 

One of the designs goals that I thought would be interesting was the concept of being able to trade points between users. 

We have other odd-ball games like 0x21 at SOTB and we wanted a shady grey market of info trading to be created. 

We want points to approximate a 'currency' during the CTF. You can send a `tip` to so someone for helping you or to settle some debt.  

One of the key features (and main reason for building this) is the ability to allow users to partcipate in the fun of creating challenges.  

They describe their challenge in a json file and send it to the automaton.

Users have to pay a percentage of the value of their challenge before it becomes available to other players. 

This is to provide *some* incentive for it to be solvable by others (not a guarantee). 

They are given a reward for every team that solves it. this can become a money maker for a team. 

For example, player1 a challenge worth 500 points costs 250 points to post. (50% of value; this is tunable) 

player2 can submit the flag for the 500 points (and possible firstblood bonus of 10% for 550 points; again tunable) 

player1 will receive a reward of 25% (125 points; also tunable).

Two separate teams will have to submit the flag in order for player1 to break even. 

They will profit on the third solve. 

Obviously, teammates can't solve your flags. 

This framework is very team oriented.

No limit on team size. 

that's all the documentation for now... 
