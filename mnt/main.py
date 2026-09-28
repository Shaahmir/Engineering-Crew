from tiny_erp.ui import create_ui

def main():
    demo = create_ui()
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)

if __name__ == "__main__":
    main()
