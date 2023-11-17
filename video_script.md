## Introduction

In the introduction section, we provide a brief overview of what a Capture The Flag (CTF) challenge is and highlight the purpose of the tutorial. We can think of CTF challenges as thrilling adventures in the world of cybersecurity, where participants work individually or in teams to solve complex problems. By using the BYOCTF platform, cybersecurity enthusiasts can create their own engaging and educational challenges for their peers.

## Setting Up the Challenge

In the "Setting Up the Challenge" section, we emphasize the importance of careful planning and consideration before creating a CTF event. It's like building a strong foundation for a house before adding the walls and roof. We discuss key factors to consider, such as infrastructure, potential interference between teams, network accessibility, cost, and complexity. It's crucial to pay attention to detail and ensure all links and files are correctly linked since once the challenge is committed, it cannot be edited.

## Shared vs. Dedicated Infrastructure

The "Shared vs. Dedicated Infrastructure" section helps participants understand the two options they have when it comes to the underlying infrastructure of their CTF challenge. We can think of shared infrastructure as a shared workspace, where participants can collaborate and work together without interference. On the other hand, dedicated infrastructure is like individual workstations, where each team has its isolated environment. It provides more control and security but comes with additional cost and complexity.

## Network Accessibility and File Hosting

In the "Network Accessibility and File Hosting" section, we explore considerations for making the challenges accessible to participants. We use an analogy of organizing a treasure hunt that can be played locally or remotely. For remote participants, the challenges need to be publicly accessible, just like hiding treasures in public spaces. When it comes to file hosting, participants need to think creatively and use reliable platforms like Google Drive, Github, or Pastebin to ensure the challenges' files are accessible for a considerable time.

## Challenge Value, Descriptions, Hints, and Rewards

The "Challenge Value, Descriptions, Hints, and Rewards" section focuses on key aspects of challenge design. We can compare the challenge value to the difficulty level of a game level or the point system in a board game. It's important to set a cumulative challenge value that exceeds a minimum threshold to keep participants engaged. We discuss the need for unique challenge titles and flags, concise challenge descriptions, and the exciting concept of hints that participants can unlock at increasing costs, similar to buying clues in a treasure hunt. The reward system ensures that challenge creators earn a portion of the points spent on hint buys, making it a win-win situation.

## Posting and Reward System

In the "Posting and Reward System" section, we dive into the cost and reward structure for challenge creators. We can think of posting a challenge as paying an entry fee to participate in a competition. The challenge creator pays a certain fee, typically a percentage of the total challenge value, to post the challenge. As participants solve parts of the challenge, the creator earns a portion of the reward, encouraging creators to design solvable challenges. It's a double-edged sword, as an unsolvable challenge would result in losing points.

## Conclusion

The conclusion wraps up the tutorial by summarizing the key points and encouraging participants to embark on their own CTF challenge creation journey. We can compare creating a CTF challenge to embarking on a thrilling adventure, where every great adventure begins with a single step. Participants are encouraged to craft their intriguing cybersecurity challenges and stay tuned for more insights and tutorials. The conclusion also emphasizes the importance of staying safe and continuously exploring the exciting world of cybersecurity.


## Single Flag Walkthrough

"Let's use our forensics challenge as an example. We're tasked with finding a hidden file in a disk image.

The TOML file for this challenge would look something like this:


```toml
author = "YourName#1234" 
challenge_title = 
"Find the Hidden File" 
challenge_description = "A disk image has been found with a hidden file. Your task is to find and analyze the file." 
uuid = "b7a8b9c1-d2e3-4567-b8c9-d0e1f2a3b4c5" # a uuid4 string. This will be unique for each challenge 
tags = [ "Forensics",]  

[[flags]] 
flag_title = "Hidden File Found" 
flag_value = 100 
flag_flag = "BYOCTF{Hidden_File_Found}"  
[[hints]] 
hint_cost = 10 
hint_text = "Have you tried looking at the deleted files?"
```

Let's break this down:

- `author`: Your username. You can use any name you like. Make sure to include your unique identifier number after the '#'.
- `challenge_title`: The title of the challenge. In our case, it's 'Find the Hidden File'.
- `challenge_description`: A brief description of what the challenge is about.
- `uuid`: A unique identifier for this challenge. You can generate one using an online UUID generator.
- `tags`: This section helps to categorize your challenge. We've used 'Forensics' in this case.

Next up is the `flags` section. Each challenge can have one or more flags. In our example, we have only one flag:

- `flag_title`: The title of the flag. We've chosen 'Hidden File Found'.
- `flag_value`: The number of points this flag is worth. We've chosen 100 points.
- `flag_flag`: The actual flag that participants need to find. Our flag is 'BYOCTF{Hidden_File_Found}'.

Finally, we have the `hints` section. Again, you can have one or more hints. Each hint costs participants a certain amount of points:

- `hint_cost`: The number of points it costs to unlock this hint. We've chosen 10 points.
- `hint_text`: The text of the hint. Our hint is 'Have you tried looking at the deleted files?'.

And that's it! That's how you set up a TOML file for a challenge in BYOCTF. I hope this walkthrough helps you understand how to structure your own challenges.

Remember, you can use the tool at [https://validator.byoctf.com/creator](https://validator.byoctf.com/creator) to aid in creating these TOML files. This can make the process much smoother and ensure your challenge is set up correctly.

## Multiflag Walkthrough

"Building on our earlier example, let's consider a more complex scenario where a challenge has multiple flags. This is often seen in real-life CTF competitions, adding depth to challenges, and giving players multiple objectives to work towards. In this case, we'll walk through a pentesting and forensics challenge, where players have to discover two flags on a server located at 3.43.54.28.

The TOML file for this challenge would look something like this:

```toml
author = "YourName#1234" challenge_title = "Server Double Trouble" challenge_description = "Two flags have been hidden on a server at 3.43.54.28. Can you find them both?" uuid = "c1d2e3f4-a567-8901-b234-c567d890e1f2" # a uuid4 string. This will be unique for each challenge 
tags = [ "Pentest", "Forensics"]  

[[flags]] 
flag_title = "Server Flag 1" 
flag_value = 100 
flag_flag = "BYOCTF{Server_Flag_1}" 
[[flags]] 
flag_title = "Server Flag 2" 
flag_value = 200 
flag_flag = "BYOCTF{Server_Flag_2}"  

[[hints]] 
hint_cost = 25 
hint_text = "Have you tried investigating the network traffic?"  
[[hints]] hint_cost = 30 
hint_text = "What about any recent user activities?"
```

As you can see, most of the fields are the same as our earlier example. But now, we have two flags and two hints:

- flag_title: The titles of the flags are 'Server Flag 1' and 'Server Flag 2'.
- flag_value: The values of the flags are 100 and 200 points respectively.
- flag_flag: The actual flags that participants need to find are 'BYOCTF{Server_Flag_1}' and 'BYOCTF{Server_Flag_2}'.
- hint_cost: The costs to unlock the hints are 25 and 30 points respectively.
- hint_text: The hints are 'Have you tried investigating the network traffic?' and 'What about any recent user activities?'.

This multi-flag setup adds more dimension to the challenge and gives participants multiple paths to gain points.

Just like with the single flag example, you can use the tool at [https://validator.byoctf.com/creator](https://validator.byoctf.com/creator) to help in creating these TOML files. This makes the challenge setup process much more straightforward and ensures everything is set up correctly.

Multi-flag challenges can be a great way to test a wider range of skills and keep participants engaged for a longer period of time. Have fun creating your challenges!"


----


[BYOCTF Logo Fades In]

Narrator: Hey there! Welcome to a quick walkthrough on creating your own challenge for BYOCTF. Today, we're going to craft a simple yet fun challenge together. No frills, just a good old-fashioned CTF puzzle.

[Screen Transition to Challenge Creator Interface]

Narrator: Alright, let's jump into the Challenge Creator App. This is where all the magic happens. Let's get cracking on our challenge, which we'll call "Log Sleuth."

[Adding the Challenge Title]

Narrator: First things first, the title. We want something catchy but clear. "Log Sleuth" sounds about right. It tells players they're going to do some detective work on logs.

[Entering the Challenge Description]

Narrator: Now for the description. This part's important — it's your chance to set the scene. Let's keep it simple: "Dive into the server logs and find the hidden message. Are you up for a bit of digital detective work?" There, that should do it.

[Inputting Tags]

Narrator: Tags are next. They're like hashtags for your challenge; they help people find your stuff. We'll go with "log-analysis" and "forensics" for this one.

[Setting Up Flags]

Narrator: Flags time! This is what players are hunting for. Our first flag is "hidden_user" and we'll make it worth 100 points. The second flag, "secret_access_code", is a bit trickier, so we'll value it at 200 points.

[Crafting Hints]

Narrator: Now, let's throw in some hints. We don't want to give the game away, but a little help can keep things fun. Hint one: "The user we're looking for starts with 'A'." That's for the first flag and will cost the player 10 points. For the second flag, we'll add: "Look for the entry after the system reboot." And that's a 20-pointer.

[Validation and Submission]

Narrator: Got everything in place? Cool. Hit the validate button to make sure your challenge plays nice with the BYOCTF rules. All good? Submit your challenge with the !byoc_commit command. It'll cost you a few points, but that's where the fun begins.

[Explaining the Reward Mechanism]

Narrator: Here's how the rewards work. You spend points to post your challenge, right? Well, every time someone solves a flag, you get a cut of the points based on its value. So, if someone cracks the "hidden_user" flag, you'll get a nice 25 points back. Solve rates for your challenge can actually earn you more points than what you spent. It's like getting a little "thank you" every time your puzzle gets solved.

[Visual of Points and Solves]

Narrator: Keep an eye on those solves. The first few will help you break even, and after that, it's all profit. Before you know it, you could be raking in more points than you put in.

[Closing Remarks]

Narrator: And there you have it — challenge creation on BYOCTF, demystified. "Log Sleuth" is ready to puzzle the minds of players, and you're all set to watch the points roll in.

[End Screen with Call to Action]

Narrator: Fancy making a challenge yourself? Head over to [website URL] and get started. If you've got any questions, or just want to chat puzzles and points, hit us up on the community channels. Catch you on the leaderboards!

