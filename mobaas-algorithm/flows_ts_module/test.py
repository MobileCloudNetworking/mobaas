import flows_ts

test_flow_data_list = [(1415976534072, 1415976546382, "38.186.48.58", "115.180.193.40", 233, 21637)
                      , (1415976534072, 1415976546276, "252.69.255.131", "206.37.104.127", 874,  81710)
                      , (1415976534072, 1415976546622, "249.120.153.88", "43.239.172.108", 2588, 223390)
                      , (1415976534072, 1415976545767, "113.119.246.64", "37.30.65.18",    120,  11544)
                      , (1415976534072, 1415976544915, "246.25.18.234",  "37.246.84.22",   8443, 715183)
                      , (1415976534072, 1415976545289, "252.50.110.46",  "100.101.144.11", 821,  76195)
                      , (1415976534072, 1415976544230, "35.119.22.201",  "37.82.243.223",  24,   2688)
                      , (1415976534072, 1415976534452, "94.158.244.121", "197.54.83.168",  25,   4500)
                      , (1415976534072, 1415976542410, "63.186.70.228",  "115.25.102.105", 8131, 683295)
                      , (1415976534072, 1415976542318, "242.187.113.6",  "42.252.1.97",    48,   5616)
                      , (1415976534072, 1415976541525, "107.238.231.33", "203.147.45.231", 24,   6000)
                      , (1415976534072, 1415976541513, "42.207.135.95",  "205.203.67.67",  3792, 319680)
                      , (1415976534072, 1415976541472, "253.155.255.33", "100.209.59.77",  24,   3168)
                      ]


print test_flow_data_list
bytes_total = 0

for a, b, c, d, e, bytes in test_flow_data_list:
    bytes_total += bytes

time_throughput_list = flows_ts.process_flow_data(test_flow_data_list)
print time_throughput_list
processed_bytes_total = 0

for f, bytes in time_throughput_list:
    processed_bytes_total += bytes

print "Total: " + str(bytes_total)
print "Processed total: " + str(processed_bytes_total)
difference = abs(bytes_total - processed_bytes_total)
print "Difference: " + str(difference)
perc = difference / bytes_total * 100
print "Difference percentage from unprocessed total: " + str(perc)