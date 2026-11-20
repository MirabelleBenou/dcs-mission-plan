"""Un .miz fabriqué à la main pour les tests d'HQ : un Mi-8MT à AdditionalArmor = false et une clé hors table, un Mi-24P sans AddPropAircraft."""
import zipfile, sys
MISSION = r'''mission =
{
    ["version"] = 19,
    ["date"] =
    {
        ["Day"] = 15,
        ["Month"] = 6,
        ["Year"] = 1985,
    }, -- end of ["date"]
    ["start_time"] = 28800,
    ["theatre"] = "Syria",
    ["weather"] =
    {
        ["atmosphere_type"] = 0,
        ["wind"] =
        {
            ["atGround"] = { ["speed"] = 3, ["dir"] = 270, },
            ["at2000"] = { ["speed"] = 5, ["dir"] = 270, },
            ["at8000"] = { ["speed"] = 8, ["dir"] = 270, },
        },
        ["season"] = { ["temperature"] = 20, },
        ["type_weather"] = 0,
        ["qnh"] = 760,
        ["cyclones"] = {},
        ["name"] = "Winter, clean sky",
        ["fog"] = { ["thickness"] = 0, ["visibility"] = 25, },
        ["visibility"] = { ["distance"] = 80000, },
        ["clouds"] = { ["thickness"] = 200, ["density"] = 0, ["base"] = 3000, ["iprecptns"] = 0, },
        ["groundTurbulence"] = 0,
        ["enable_fog"] = false,
        ["dust_density"] = 0,
        ["enable_dust"] = false,
    }, -- end of ["weather"]
    ["coalition"] =
    {
        ["blue"] =
        {
            ["name"] = "blue",
            ["country"] =
            {
                [1] =
                {
                    ["id"] = 2,
                    ["name"] = "USA",
                    ["helicopter"] =
                    {
                        ["group"] =
                        {
                            [1] =
                            {
                                ["groupId"] = 1,
                                ["name"] = "HIND",
                                ["task"] = "Transport",
                                ["frequency"] = 251,
                                ["modulation"] = 0,
                                ["x"] = 100,
                                ["y"] = 200,
                                ["route"] =
                                {
                                    ["points"] =
                                    {
                                        [1] =
                                        {
                                            ["type"] = "Turning Point",
                                            ["action"] = "Turning Point",
                                            ["x"] = 100,
                                            ["y"] = 200,
                                            ["alt"] = 500,
                                            ["alt_type"] = "BARO",
                                            ["speed"] = 50,
                                            ["task"] = { ["id"] = "ComboTask", ["params"] = { ["tasks"] = {}, }, },
                                        },
                                    },
                                },
                                ["units"] =
                                {
                                    [1] =
                                    {
                                        ["unitId"] = 1,
                                        ["name"] = "HIND-1",
                                        ["type"] = "Mi-8MT",
                                        ["skill"] = "Client",
                                        ["x"] = 100,
                                        ["y"] = 200,
                                        ["alt"] = 500,
                                        ["callsign"] = { [1] = 1, [2] = 1, [3] = 1, ["name"] = "Enfield11", },
                                        ["onboard_num"] = "011",
                                        ["livery_id"] = "standard",
                                        ["payload"] =
                                        {
                                            ["pylons"] = {},
                                            ["fuel"] = "1929",
                                            ["flare"] = 128,
                                            ["chaff"] = 0,
                                            ["gun"] = 100,
                                        }, -- end of ["payload"]
                                        ["AddPropAircraft"] =
                                        {
                                            ["AdditionalArmor"] = false,
                                            ["zzUnknownKey"] = "garder",
                                        }, -- end of ["AddPropAircraft"]
                                    }, -- end of [1]
                                },
                            },
                            [2] =
                            {
                                ["groupId"] = 2,
                                ["name"] = "CAESAR",
                                ["task"] = "CAS",
                                ["frequency"] = 251,
                                ["modulation"] = 0,
                                ["x"] = 300,
                                ["y"] = 400,
                                ["route"] =
                                {
                                    ["points"] =
                                    {
                                        [1] =
                                        {
                                            ["type"] = "Turning Point",
                                            ["action"] = "Turning Point",
                                            ["x"] = 300,
                                            ["y"] = 400,
                                            ["alt"] = 500,
                                            ["alt_type"] = "BARO",
                                            ["speed"] = 60,
                                            ["task"] = { ["id"] = "ComboTask", ["params"] = { ["tasks"] = {}, }, },
                                        },
                                    },
                                },
                                ["units"] =
                                {
                                    [1] =
                                    {
                                        ["unitId"] = 2,
                                        ["name"] = "CAESAR-1",
                                        ["type"] = "Mi-24P",
                                        ["skill"] = "Client",
                                        ["x"] = 300,
                                        ["y"] = 400,
                                        ["alt"] = 500,
                                        ["callsign"] = { [1] = 2, [2] = 1, [3] = 1, ["name"] = "Springfield11", },
                                        ["onboard_num"] = "021",
                                        ["livery_id"] = "standard",
                                        ["payload"] =
                                        {
                                            ["pylons"] = {},
                                            ["fuel"] = 1701,
                                            ["flare"] = 192,
                                            ["chaff"] = 0,
                                            ["gun"] = 100,
                                        }, -- end of ["payload"]
                                    }, -- end of [1]
                                },
                            },
                        },
                    },
                },
            },
        },
        ["red"] =
        {
            ["name"] = "red",
            ["country"] =
            {
                [1] = { ["id"] = 0, ["name"] = "Russia", },
            },
        },
        ["neutrals"] = { ["name"] = "neutrals", ["country"] = {}, },
    }, -- end of ["coalition"]
} -- end of mission
'''
def make(path):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mission', MISSION)
        z.writestr('theatre', 'Syria')
        z.writestr('options', 'options = {}\n')
if __name__ == '__main__':
    make(sys.argv[1])
