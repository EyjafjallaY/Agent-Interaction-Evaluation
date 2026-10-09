import argparse
import json
from pathlib import Path
import pandas as pd


def main():
    parser = argparse.ArgumentParser(description="Digital-human multimodal interaction analysis")
    sub = parser.add_subparsers(dest='command',required=True)
    demo = sub.add_parser('demo',help='Generate synthetic inputs and run the archived notebook profile')
    demo.add_argument('--out',type=Path,required=True)
    demo.add_argument('--seed',type=int,default=2026)
    run = sub.add_parser('run',help='Analyze locally held canonical CSV inputs')
    run.add_argument('--questionnaire',type=Path,required=True)
    run.add_argument('--frames',type=Path,required=True)
    run.add_argument('--events',type=Path,required=True)
    run.add_argument('--out',type=Path,required=True)
    for p in [demo,run]:
        p.add_argument('--no-plots',action='store_true')
    args = parser.parse_args()
    from .pipeline import analyze
    if args.command == 'demo':
        from .synthetic import generate_demo
        q,f,e = generate_demo(seed=args.seed)
    else:
        inputs = [args.questionnaire.resolve(),args.frames.resolve(),args.events.resolve()]
        output = args.out.resolve()
        if any(output == p.parent or output in p.parents for p in inputs):
            parser.error('Choose a dedicated output directory away from input files')
        q,f,e = [pd.read_csv(p,dtype={'Participant_ID':str}) for p in inputs]
        for table in [q,f,e]:
            table.columns = table.columns.str.strip()
            if table.columns.duplicated().any():
                parser.error('Duplicate columns after header whitespace normalization')
    report = analyze(q,f,e,args.out,synthetic=args.command=='demo',plots=not args.no_plots)
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
