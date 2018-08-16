import vkautoreply


def main():
    init_tests = vkautoreply.TestingOfInitialConditions()
    init_tests.run_all_test()
    configs = vkautoreply.MainConfig()
    accounts = configs.load_vk_cliens()
    pipline = vkautoreply.Facade()
    for account in accounts:
        pipline.add(account)
    pipline.set_time_for_sleep(configs.get_time_for_sleep())
    pipline.start()


if __name__ == '__main__':
    main()
