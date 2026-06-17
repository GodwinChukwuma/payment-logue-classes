from pci_api import scheduler

if __name__ == "__main__":
    scheduler.start()
    import time

    while True:
        time.sleep(60)
        
