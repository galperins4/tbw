from park.park import Park

park = Park(
    '127.0.0.1',
    4002,
    '578e820911f24e039733b45e4882b73e301f813a0d2c31330dafda84534ffa23',
    '1.1.1'
)

last_block = park.blocks().blocks({
                                "limit": 1
                                })
                                
print(last_block)                                
