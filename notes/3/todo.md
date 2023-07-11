- Find more readings
  - Endianness trade-offs on different CPUs and generally
  - Binary serialization formats
    - Protobuf wire format
    - Cap'n'proto format
    - https://flatbuffers.dev/
    - Python pickle format
      - https://github.com/cloudpipe/cloudpickle
    - Java serialization format
    - JSON binary serialization
      - BSON
      - MessagePack
      - CBOR
    - Parquet
    - HDF5
    - Avro
  - Textual serialization formats
    - JSON
    - YAML
    - TOML
  - Parsers/deserializers
    - Python
      - https://github.com/simdjson/simdjson
      - https://github.com/ultrajson/ultrajson
    - C++
      - https://github.com/nlohmann/json
      - https://miloyip.github.io/rapidjson/
      - https://github.com/vivkin/gason
  - Streaming parsers
  - https://seriot.ch/projects/parsing_json.html
  - https://cs-syd.eu/posts/2022-08-22-how-to-deal-with-money-in-software
  - https://www.zainrizvi.io/blog/falsehoods-programmers-believe-about-time-zones/
  - Floats
    - https://en.wikipedia.org/wiki/Unum_(number_format)
      - https://www.cs.cornell.edu/courses/cs6120/2019fa/blog/posits/
    - https://en.wikipedia.org/wiki/Unit_in_the_last_place
    - https://float.exposed/
    - https://randomascii.wordpress.com/category/floating-point/
    - https://randomascii.wordpress.com/2012/02/11/they-sure-look-equal/
    - https://docs.oracle.com/cd/E19957-01/806-3568/ncg_goldberg.html
    - https://0.30000000000000004.com/
    - https://www.zverovich.net/slides/2019-04-fp.pdf
    - https://github.com/jk-jeon/dragonbox
  - https://github.com/fmtlib/fmt
  - Memory allocation
    - Physical page
      - https://en.wikipedia.org/wiki/Slab_allocation
      - https://en.wikipedia.org/wiki/Buddy_memory_allocation
    - https://github.com/microsoft/mimalloc
    - https://github.com/mjansson/rpmalloc
    - https://github.com/emeryberger/Hoard
    - https://github.com/plasma-umass/Mesh
    - https://github.com/google/tcmalloc
    - https://github.com/jemalloc/jemalloc/wiki/Background
    - https://sourceware.org/glibc/wiki/MallocInternals
      - https://dangokyo.me/2017/12/05/introduction-on-ptmalloc-part1/
    - https://www.gingerbill.org/series/memory-allocation-strategies/
      - https://github.com/mtrebi/memory-allocators
    - https://ruby0x1.github.io/machinery_blog_archive/post/virtual-memory-tricks/index.html
  - https://people.freebsd.org/~lstewart/articles/cpumemory.pdf
  - https://www.postgresql.org/docs/current/storage-toast.html
  - Garbage collection algorithms
    - https://en.wikipedia.org/wiki/Garbage_collection_(computer_science)
    - Reference counting
    - Mark and sweep
    - Copying GC
    - https://github.com/deephacks/awesome-jvm#garbage-collectors
  - https://martin.kleppmann.com/2012/12/05/schema-evolution-in-avro-protocol-buffers-thrift.html
  - https://www.upsolver.com/blog/the-file-format-fundamentals-of-big-data
  - https://web.archive.org/web/20220529231010/https://ourmachinery.com/post/
  - https://gist.github.com/simonrenger/d1da2a10d11f8a971fc6f1b574ab3e99#great-youtube-videos
  - https://github.com/rain-1/awesome-allocators#general-learning