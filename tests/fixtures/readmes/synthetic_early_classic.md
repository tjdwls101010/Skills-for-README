# fdx

A simple, fast alternative to `find`.

![demo of fdx searching a source tree](doc/screencast.gif)

`fdx` searches your filesystem the way you usually mean it: `fdx PATTERN`
instead of `find -iname '*PATTERN*'`. It skips hidden files and anything in
`.gitignore` unless you ask for them.

## Install

Requires Rust 1.70 or newer. Nothing else.

```bash
cargo install fdx
```

Then run it in any directory:

```bash
$ fdx netfl
netflix/
netflix/client.rs
```

Three matches in a 12,000-file tree take about 40 ms here. `find -iname` is
roughly as fast on a warm cache; the difference shows up on cold caches and
on trees with a large `.gitignore`.

## License

`fdx` is dual-licensed under MIT and Apache-2.0. See [LICENSE-MIT](LICENSE-MIT).
