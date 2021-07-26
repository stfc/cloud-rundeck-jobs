import argparse
from queryopenstack.query import Query

if __name__ == '__main__':
    # ARGPARSE BOILERPLATE CODE TO READ IN INPUTS
    parser = argparse.ArgumentParser(description='Get Information From Openstack')

    parser.add_argument("search_by", help="Search For Specific Resource Type",
    nargs=1, choices =["project", "host", "ip", "user", "server"])
    parser.add_argument('-s', "--select", nargs="+", help="properties to get")
    parser.add_argument('-w', "--where", nargs="+", action='append',
    help="selection policy", metavar=('policy', '*args'))

    parser.add_argument("--sort-by", nargs="+")

    parser.add_argument("--no-output", default=False, action="store_true")
    parser.add_argument("--save", default=False, action="store_true")
    parser.add_argument("--save-path", type=str, default="./Logs/")

    args = parser.parse_args()

    Query(by=args.search_by[0],
          properties_list=args.select,
          criteria_list=args.where if args.where else None,
          sort_by_list=args.sort_by if args.sort_by else None,
          output_to_console=(not args.no_output),
          save=args.save,
          save_path=args.save_path
          )
