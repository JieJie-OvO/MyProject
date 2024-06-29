from selenium import webdriver

edge_browser_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
edge_driver_path = r"E:\DevWorkStation\BrowserDriver\Edge\msedgedriver.exe"


def get_edge_driver(
    browser_path: str = edge_browser_path, driver_path: str = edge_driver_path
) -> webdriver.Edge:
    edge_options = webdriver.EdgeOptions()
    edge_options.binary_location = browser_path
    edge_options.add_argument("--headless")
    edge_service = webdriver.EdgeService(executable_path=driver_path)
    driver = webdriver.Edge(service=edge_service, options=edge_options)
    return driver
