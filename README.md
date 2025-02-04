The anki deck for the Dictionary of Japanese Grammar, but with furigana and audio. Of course this could not exist without the [original DoJG deck](https://dojgdeck.neocities.org/#anon) as well as the DoJG itself ([index](https://core6000.neocities.org/dojg/)).

## Installation

### Decks

The decks can be found in the [finished_decks](https://github.com/XaviACLM/dojg-furigana/tree/master/finished_decks) directory. +F means the deck has furigana and +A means the deck has audio - pick and choose. The option without either is mostly there for completeness, but it does have some minor differences with vanilla DoJG, explained in §Differences. To install this you simply have to download whichever .apkg file you like and drag it into anki. If you already use a dojg deck, consider using [this other repository](https://github.com/XaviACLM/anki-sched-transfer) to transfer scheduling data between cards.

### Media

**The media (.wav files) have to be downloaded separately.** Downloads are available [here](https://www.mediafire.com/folder/nsrnc8yanphn0/DoJG_sentence_audio_zips). Obviously this only neccessary if you use one of the +A decks.

You will need to manually insert the media into Anki's files. In windows, this is easy - go to `%appdata%/Anki2/your-anki-username/collection.media`, create in this folder another folder called `dojg_sentence_audio`, and paste within it all the .wav files you have downloaded. For other operating systems you'll have to figure out where Anki keeps its `collections.media` folder, but this should be easy enough.

The media isn't packed into the .apkg files because i couldn't get it working, but also because there is over 2GB of audio. For this reason the downloads are zipped, but more importantly, partial downloads are offered - corresponding to the 'Basic' and 'Intermediate' parts of the dictionary. These are used just the same as the full audio folder, just dump every .wav file into `collections.media/dojg_sentence_audio` - you can mix and match if you want (i.e. put the 'Basic' and 'Intermediate' parts but not advanced). This won't break any of the cards, you'll just find that the play buttons do nothing if you haven't downloaded the corresponding audio.

Keep in mind that the amount of grammatical concepts in each part of the dictionary is pretty similar, but because the simpler parts tend to use simpler differences, the download for the basic part is quite a lot lighter than the intermediate, and likewise intermediate is lighter than advanced.

### Clozes

I do not use cloze cards so I haven't tested that the deck works for them, but all the html tags relating to clozes are left untouched - so it *should* work if you add a cloze card type like in [the original deck](https://dojgdeck.neocities.org/#anon). If you do this feel free to let me know if it works.

## Some notes

### On correctness

Neither the audio nor the furigana is 100% correct. I decided it was good enough when I couldn't spot a mistake out of 50 randomly picked sentences, but your mileage may vary - none of the morphologic analyzers (or tts-es, for that matter) are 100% accurate.

### On completeness

Not everything in the deck has furigana. The two exceptions are:

- The titles (names, 'grammatical concept') of each card. This is because they are often just a part of speech excised from context, which makes the morphological parser misinterpret them - e.g. if you just give it 間 by itself it may read it as けん where あいだ is intended. In any case the titles usually already provide furigana (in parentheses) in the original deck, which is transferred over to this deck.
- A single sentence - a passage of 夢 by Ryūnosuke Akutagawa, which contained like five or six kanji uncommon enough to give the morphological parser trouble. I couldn't be bothered adding them all to the dictionary.

### On autoplay

The back of the card will autoplay the audio of all the sentences in order. The front of the card will only play one. The reason for this is in §HTML.

### Is a grammar deck even a sound concept?

As with everything relating to using anki for language: it's very useful so long as it's not the only thing you do. Particularly you should never use this to *start* learning grammar - but once you know how japanese syntax works in general, I think this is a perfectly fine main learning resource for grammar so long as you get your practice elsewhere. You don't really need a book to explain to you what ほど or 場合 mean - once you have a basic grasp on the language, a quick explanation and a bunch of examples are good enough to get going - which is exactly what the DoJG deck is.

Consider looking through the [online index](https://dojgdeck.neocities.org/#anon) for the DoJG for any sticking points.

### On random example sentences

This is based off of the anon random version of the [DoJG deck](https://dojgdeck.neocities.org/#anon) in neocities. This is just the standard DoJG deck with the card html edited such that the front side shows a random subset of the example sentences on the back, this subset changing for each card each day. Generally speaking example sentences are a great addition to any sort of language deck *as long as* they aren't regular enough that you'll recognize the sentences instead of the word/concept - this is specifically avoided by having the front only show a random subset of the back. Your mileage may vary on whether you end up recognizing the sentences anyway (there's only about 5-10 per example), though personally I don't end up recognizing them very often.

I really love this idea of rotating through a sufficiently large subset of example sentences - I'm also working on an anki extension to generate example sentences for each card in a language deck.

## Implementation

Notes on implementation. This is only relevant if you're interested in running this yourself.

### Dependencies

Obviously this requires a number of python packages. A couple less obvious dependencies are:

- A package to add furigana. I use [my own fork of MikimotoH/furigana](https://github.com/XaviACLM/furigana), because the original has some bugs in `split_okurigana` - keep in mind that there are at least a dozen forks fixing this bug, so it's fine if you've already got something else working. Instructions on installing this as a python package are in the corresponding readme. My fork is a bit hacked together, e.g. i'm not even sure `__main__.py` works - we don't need any of that for this, but i'll get around to cleaning it up someday.
  - You'll need to install MeCab and its corresponding python library. MeCab needs a dictionary - I don't recall if it comes packaged with one by default, but I use ipadic. You'll need to add a few words to the dictionary for everything in the library to be parseable by MeCab - there's a file in `src`, `write_to_custom.py`, that does just this, adding the exact words that are missing - this file exists because adding words to the dictionary is a bit finnicky what with the need to use different encodings. You have to run this file from the same directory as the dictionary contents, which will usually be in `Program Files/MeCab/dic`.
- TTS software. `tts.py` contains managers for Voicevox, [w-okada's tts](https://github.com/w-okada/ttsclient), and Voicepeak. Any of the three should work. Keep in mind that (a) Voicepeak is quite expensive and (b) w-okada probably has the nicest-sounding synthesized audio, but has much lower accuracy than the other two, often mispronouncing or dropping entire words - only use it if you can double-check the correctness of all the synthesized audio.

### General workings

The program runs when you run main.py. The .apkg for the original DoJG deck needs to be in the working directory (this is already in the repo). `deck_wrangling.py` provides the interface the .apkg files. `main.py` uses this to open the original deck and apply a function to each card - this function goes through the fields containing example sentences, separates out the html from the text itself, and for each sentence generates:
- Furigana. This is done by an external package, [my own fork of MikimotoH/furigana](https://github.com/XaviACLM/furigana). The furigana is generated for the whole sentence in one go, but then has to be separated at the parts where an html tag needs to be inserted (primarily to denote clozes). When this html tag is inserted in the middle of a run of kanji, the furigana is naively split according to the length of kanji left on each side.
- Audio. After having eliminated the html, it is also important to process certain punctuation marks - e.g. some of the sentences will look like "これは本だ・です", where the ・ is meant to separate two different options 'だ' vs. 'です' for informal/formal. It'd be a bit awkward for the audio to just read this out as is, so some functions in `special_punctuation_handling.py` turn this into just "これは本だ" - by default the more informal reading is used. The sentence that ends up getting read out loud is hashed (`util.py`) to provide an id, generated, saved to `dojg_sentence_audio`, and inserted into the card.

The changes are then saved into an .apkg specified by the script. Flags passed to the field processor control whether audio or furigana gets skipped. There is some extra logic for things such as using the correct narrators for gendered speech (e.g. かい).

### Changes to the original deck

Other than the furigana and audio, i mean.

Some typos (mainly [ghost characters](https://en.wikipedia.org/wiki/Ghost_characters)) are fixed - not that I found them myself, it's just the parts of the deck that MeCab failed to recognize as words. Some kyujitai characters are substituted for their shinjitai forms, again to avoid giving MeCab trouble. To keep card names unique (this is necessary for the schedule information transfer), (1), (2) tags and such are added to some cards - DoJG already uses a lot of these, but some specific cards do not use them, so they are added.

I did look through the list of all 'duplicated card names', and, though the difference can be quite subtle at times, most of them looked like they covered different aspects of the same word. Notable exceptions to this are 'も〜も' and 'Relative Clause' - I didn't think it was a good idea to remove them, but as best as i can tell the two versions of these two cards cover the exact same concept - you might want to remove one of them.

There are also some changes to the card html:

### HTML

The html/css for the cards can be found in `src/html`

I'm not good with html/css/javascript and 'within Anki' probably isn't the best place to learn. No promises that this doesn't end up breaking. Nonetheless i did change a few things - It's best to start by explaining how the HTML works in the anon-random version of the original deck: There is an html element, `questionBox` containing all the example sentences (with hover-over translations and everything), and another html element `questionBox` that starts out empty. Some javascript code in the front of the card selects some random sentences from answerBox and *moves* (doesn't copy, moves) them over to `questionBox`. The front of the card then shows the selected example sentences (`questionBox`), as well as the name of the concept itself, and the back shows these same two things but adds the rest of the sentences (`answerBox`) and explanations/translations of the grammar concept.

The way this works provides an issue for using audio: for the back of the card, we want to take advantage of anki's autoplay, which will automatically play the audio elements of the card in the order in which they are found in its fields. This means that we have to display the example sentences on the card in the same order that they appear on the fields, or the autoplay will read them out of order, which is very confusing - but this process of separating some examples into `questionBox` and displaying it on top of the rest changes the order of the cards, so we can't use that.

For that reason we edit the javascript such that `questionBox` copies instead of cutting, and the back of the card does not display `questionBox` at all, just `answerBox`, which still has all the sentences in their original order. The sentences that appear in `questionBox` are softly highlighted in `answerBox`. Now, the autoplay for the back of the cards reads all the sentences in the correct order.

The autoplay cannot be used for the front of the card (since not all sentences will be there), so we use javascript to automatically click the first play button - so for the front of the card only the first audio is played. As best I can tell there is no way to make it so that the following buttons are pressed after the first audio is done, or even after a fixed delay (you can try this yourself - something about the environment in which the javascript is run makes it so that any attempt at timing has *strange* results).

I also changed the colors a bit to my own tastes - they are very easy to play around with in the styling sheet.

This is also a good place to mention that some of the DoJG versions seem to contain images from the DoJG (the actual book), but i'm not too sure where to find those and I don't feel they're very necessary either, so I didn't make any effort to support them.
