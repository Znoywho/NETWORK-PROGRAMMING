def decrypt(cr):
    kq = ""
    result = ""
    D_decrypt = {
            0: ".",
            1: "x",
            2: "o"
            }
    dem = 0
    luu = None
    for row in cr.diagram:
        for cell in row:
            if cell == luu:
                dem += 1
            luu = cell
            kq += D_decrypt[cell]
            dem = 1
    if dem > 1:
        kq += str(dem)


from caro import caro
